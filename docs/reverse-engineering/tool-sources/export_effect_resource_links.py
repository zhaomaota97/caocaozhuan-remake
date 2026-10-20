"""Join the native effect dispatch table with named effects, clips, and sounds."""
import csv
import json
from pathlib import Path
import pefile
import frida
from export_map_layouts import entries
from export_mcall_clips import parse

ROOT=Path(__file__).resolve().parents[1]


def main():
    pe=pefile.PE(str(ROOT/'Ekd5.exe'))
    mapping=pe.get_data(0x866c0,68)
    with (ROOT/'analysis/effects.csv').open(encoding='utf-8-sig') as f:
        names={int(r['id']):r['name_gbk'] for r in csv.DictReader(f)}
    meff=dict(entries(ROOT/'Meff.e5'))
    rows=[];clip_codes=[]
    for effect,code in enumerate(mapping):
        row=dict(effect_id=effect,name=names[effect],dispatch_code=code,resource='',entry='',sound='')
        if code==255:row['resource']='none'
        elif code<100:
            if code not in meff:raise ValueError('Meff entry missing')
            clip=parse(meff[code])
            row.update(resource='Meff.e5',entry=code,sound=f'Se_m_{clip["extra"] & 255:02d}.wav')
            if not (ROOT/row['sound']).is_file():raise ValueError('Meff sound missing')
        else:
            path=ROOT/f'Mcall{code%100:02d}.e5';clip=parse(path.read_bytes())
            row.update(resource=path.name,entry=0,sound=f'Se_m_{clip["extra"] & 255:02d}.wav')
            if not (ROOT/row['sound']).is_file():raise ValueError('Clip sound missing')
            clip_codes.append(code)
        rows.append(row)
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(codes){
  const b=Process.mainModule.base;let filename=null;
  const capture=new NativeCallback((_obj,name,_buffer,_size)=>{
    filename=name.readCString();return 1;
  },'uint',['pointer','pointer','pointer','uint'],'thiscall');
  Interceptor.replace(b.add(0x2f7f),capture);Interceptor.flush();
  const pixels=Memory.alloc(0x44c00),view=b.add(0xae4c8);
  view.add(4).writeU32(0x44c00);view.add(12).writePointer(pixels);view.add(16).writeU8(1);
  const select=new NativeFunction(b.add(0x217ff),'void',['pointer','uint'],'thiscall');
  return codes.map(code=>{filename=null;select(ptr(0),code);return {code,filename};});
}};
''')
        script.load();native=script.exports_sync.verify(clip_codes)
        for row in native:row['match']=row['filename'].upper()==f'MCALL{row["code"]%100:02d}.E5'
        with (ROOT/'analysis/effect-resource-links.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        (ROOT/'analysis/native-effect-clip-links-validation.json').write_text(
            json.dumps(native,indent=2),encoding='utf-8')
        print(f'Linked {len(rows)} effects; native clip filenames {sum(r["match"] for r in native)}/{len(native)}')
        if len(native)!=9 or not all(r['match'] for r in native):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
