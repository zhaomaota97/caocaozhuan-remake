"""Validate mode-7 transparent portrait blitting on all decoded FACE entries."""
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]


def main():
    faces = [dict(index=i, pixels=list(raw)) for i, raw in entries(ROOT / 'Face.e5')]
    device = frida.get_local_device()
    runtime = ROOT / 'analysis/runtime-game'
    pid = device.spawn([str(runtime / 'Ekd5.exe')], cwd=str(runtime))
    session = None
    try:
        session = device.attach(pid)
        script = session.create_script('''
rpc.exports = { verify(faces) {
 const fn = new NativeFunction(Process.mainModule.base.add(0x7F740), 'void',
  ['int','int','int','int','pointer','pointer','int'], 'mscdecl');
 const source = Memory.alloc(5120), destination = Memory.alloc(72*80);
 const rows=[];
 for (const face of faces) {
  source.writeByteArray(face.pixels);
  destination.writeByteArray(new Uint8Array(72*80).fill(165));
  fn(64,80,72,64,source,destination,7);
  const actual=new Uint8Array(destination.readByteArray(72*80));
  let mismatch=0, transparent=0;
  for(let y=0;y<80;y++) for(let x=0;x<72;x++) {
   const pixel=x<64?face.pixels[y*64+x]:0;
   const expected=x<64&&pixel!==0?pixel:165;
   if(actual[y*72+x]!==expected)mismatch++;
   if(x<64&&pixel===0)transparent++;
  }
  rows.push({index:face.index,mismatch,transparent});
 }
 return rows;
}};
''')
        script.load()
        rows = script.exports_sync.verify(faces)
        report = dict(function='0x47F740', mode=7, draw_mode=4,
                      scope='all FACE bytes, 64x80, source stride64, destination stride72; zero skip and padding preservation; no window or palette upload',
                      passed=sum(r['mismatch'] == 0 for r in rows), total=len(rows), rows=rows)
        (ROOT / 'analysis/native-portrait-blit-validation.json').write_text(
            json.dumps(report, indent=2), encoding='utf-8')
        print(f'Native portrait transparent blit: {report["passed"]}/{len(rows)}')
        if report['passed'] != len(rows):
            raise SystemExit(1)
    finally:
        if session:
            session.detach()
        device.kill(pid)


if __name__ == '__main__':
    main()
