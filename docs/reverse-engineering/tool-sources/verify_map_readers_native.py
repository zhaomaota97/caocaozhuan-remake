"""Validate native map accessors against decoded shipped map resources."""
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]


def main():
    payload = {key:[dict(id=i, bytes=list(raw)) for i, raw in entries(ROOT / filename)]
               for key, filename in [('terrain','Hexzmap.e5'),('pmap','Pmap.e5')]}
    device = frida.get_local_device()
    lab = ROOT / 'analysis/runtime-game'
    pid = device.spawn([str(lab / 'Ekd5.exe')], cwd=str(lab))
    session = None
    try:
        session = device.attach(pid)
        script = session.create_script('''
rpc.exports = {verify(payload) {
  const b = Process.mainModule.base, view = b.add(0xaeb38);
  const terrainAt = new NativeFunction(b.add(0x35991), 'uint8', ['pointer'], 'mscdecl');
  const arrayAt = new NativeFunction(b.add(0x270d3), 'uint16',
      ['uint16','uint16','uint16'], 'mscdecl');
  const coord = Memory.alloc(2), results = [];
  function install(bytes) {
    const buffer = Memory.alloc(bytes.length); buffer.writeByteArray(bytes);
    view.add(4).writeU32(bytes.length); view.add(12).writePointer(buffer);
    view.add(16).writeU8(1); return buffer;
  }
  for (const map of payload.terrain) {
    const width = Math.floor(map.bytes[0]/3), height = Math.floor(map.bytes[1]/3);
    const bytes = new Uint8Array(0x640 + width*height);
    bytes.set(map.bytes.slice(2),0x640); const keep = install(bytes);
    b.add(0xb422c).writeU8(width); b.add(0xb422d).writeU8(height);
    let checks = 0, failures = 0;
    for (let y=0; y<height; y++) for (let x=0; x<width; x++) {
      coord.writeU8(x); coord.add(1).writeU8(y); checks++;
      if (terrainAt(coord) !== map.bytes[2+y*width+x]) failures++;
    }
    for (const [x,y] of [[width,0],[0,height],[255,255]]) {
      coord.writeU8(x); coord.add(1).writeU8(y); checks++;
      if (terrainAt(coord) !== 255) failures++;
    }
    results.push({kind:'terrain',id:map.id,checks,failures});
  }
  for (const map of payload.pmap) {
    const keep = install(map.bytes);
    const word = offset => map.bytes[offset] + 256*map.bytes[offset+1];
    const width=word(2), height=word(4), depth=word(6);
    let checks=0, failures=0;
    for (let z=0; z<depth; z++) for (let y=0; y<height; y++) for (let x=0; x<width; x++) {
      const expected = word(16+2*(z*width*height+y*width+x)); checks++;
      if (arrayAt(x,y,z) !== expected) failures++;
    }
    for (const [x,y,z] of [[width,0,0],[0,height,0],[0,0,depth],[65535,65535,65535]]) {
      checks++; if (arrayAt(x,y,z) !== 0xf000) failures++;
    }
    results.push({kind:'pmap',id:map.id,checks,failures});
  }
  return results;
}};
''')
        script.load()
        rows = script.exports_sync.verify(payload)
        checks = sum(r['checks'] for r in rows)
        failures = sum(r['failures'] for r in rows)
        (ROOT / 'analysis/native-map-reader-validation.json').write_text(
            json.dumps(dict(checks=checks, failures=failures, maps=rows), indent=2), encoding='utf-8')
        print(f'Native map reader checks: {checks-failures}/{checks} across {len(rows)} maps')
        if len(rows) != 132 or failures:
            raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:
                session.detach()
            except frida.InvalidOperationError:
                pass


if __name__ == '__main__':
    main()
