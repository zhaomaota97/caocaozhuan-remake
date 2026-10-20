"""Compare original pixel mixers to the recovered Python formulas."""
import itertools
import json
from pathlib import Path
import frida
from export_map_layouts import entries
from export_mcall_clips import parse
from effect_blend import masked_pixel,constant_pixel

ROOT=Path(__file__).resolve().parents[1]


def main():
    current=bytes(v>>4 for v in dict(entries(ROOT/'Spalet.e5'))[0])
    clip=(ROOT/'Mcall00.e5').read_bytes();offset=parse(clip)['palette_offsets'][0]
    alternate=clip[offset:offset+768]
    source=list(range(256))*6;masks=[m for m in (0,1,64,128,254,255) for _ in range(256)]
    background=[(i*13+61)&255 for i in range(len(source))]
    cases=[dict(kind='masked',strength=s,alternate=a) for s,a in itertools.product((0,1,8,16),(False,True))]
    cases += [dict(kind='constant',opacity=o,invert=i,strength=s,alternate=a)
              for o,i,s,a in itertools.product((0,1,8,16),(0,1),(0,1,8,16),(False,True))]
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(current,alternate,source,masks,background,cases){
  const b=Process.mainModule.base;
  function alloc(bytes){const p=Memory.alloc(bytes.length);p.writeByteArray(bytes);return p;}
  b.add(0x97770).writeByteArray(current);
  const build=new NativeFunction(b.add(0x2fcc6),'void',['pointer'],'mscdecl');build(b.add(0x97770));
  const palette=alloc(alternate),src=alloc(source),mask=alloc(masks),bg=alloc(background);
  const dest=Memory.alloc(source.length+32);
  const masked=new NativeFunction(b.add(0x300c8),'void',
    ['int','int','pointer','pointer','pointer','pointer','pointer','uint8'],'mscdecl');
  const constant=new NativeFunction(b.add(0x2fd5a),'void',
    ['int','int','pointer','pointer','pointer','uint8','int','pointer','uint8'],'mscdecl');
  const outputs=cases.map(c=>{
    dest.writeByteArray(new Uint8Array(source.length+32).fill(165));
    const p=c.alternate?palette:ptr(0);
    if(c.kind==='masked')masked(source.length,1,src,mask,bg,dest.add(16),p,c.strength);
    else constant(source.length,1,src,bg,dest.add(16),c.opacity,c.invert,p,c.strength);
    return Array.from(new Uint8Array(dest.readByteArray(source.length+32)));
  });
  return {lookup:Array.from(new Uint8Array(b.add(0xb1b28).readByteArray(4096))),outputs};
}};
''')
        script.load();actual=script.exports_sync.verify(list(current),list(alternate),source,masks,background,cases)
        rows=[];lookup=actual['lookup']
        for case,output in zip(cases,actual['outputs']):
            palette=alternate if case['alternate'] else current
            if case['kind']=='masked':
                pixels=[masked_pixel(s,m,b,palette,current,lookup,case['strength']) for s,m,b in zip(source,masks,background)]
            else:
                pixels=[constant_pixel(s,b,palette,current,lookup,case['opacity'],case['invert'],case['strength']) for s,b in zip(source,background)]
            rows.append(dict(**case,pixels=len(pixels),match=output==[165]*16+pixels+[165]*16))
        (ROOT/'analysis/native-effect-blend-validation.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Native effect blend: {sum(r["match"] for r in rows)}/{len(rows)} batches, {sum(r["pixels"] for r in rows)} pixels')
        if len(rows)!=72 or not all(r['match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
