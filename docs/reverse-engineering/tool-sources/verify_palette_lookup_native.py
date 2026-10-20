"""Compare independently generated lookup tables to the native palette builder."""
import hashlib
import json
from pathlib import Path
import frida
from export_map_layouts import entries
from export_mcall_clips import parse
from game_palette import color_lookup

ROOT=Path(__file__).resolve().parents[1]


def main():
    clip=(ROOT/'Mcall00.e5').read_bytes();offset=parse(clip)['palette_offsets'][0]
    palettes=[bytes(v>>4 for v in dict(entries(ROOT/file))[0])
              for file in ('Spalet.e5','Pmpalet.e5')]+[clip[offset:offset+768]]
    names=['Spalet entry 0','Pmpalet entry 0','Mcall00 embedded']
    expected=[color_lookup(palette) for palette in palettes]
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(palettes){
  const b=Process.mainModule.base;
  const build=new NativeFunction(b.add(0x2fcc6),'void',['pointer'],'mscdecl');
  return palettes.map(palette=>{
    const p=Memory.alloc(768);p.writeByteArray(palette);build(p);
    return Array.from(new Uint8Array(b.add(0xb1b28).readByteArray(4096)));
  });
}};
''')
        script.load();actual=script.exports_sync.verify([list(p) for p in palettes])
        rows=[dict(palette=name,entries=4096,match=want==bytes(got),
                   sha256=hashlib.sha256(want).hexdigest())
              for name,want,got in zip(names,expected,actual)]
        (ROOT/'analysis/native-palette-lookup-validation.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Native palette lookup: {sum(r["match"] for r in rows)}/{len(rows)} tables, 12288 entries')
        if len(rows)!=3 or not all(r['match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
