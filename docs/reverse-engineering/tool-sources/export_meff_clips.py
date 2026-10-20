"""Recover all Meff clip timelines and validate native layout and audio routing."""
import json
from pathlib import Path
import frida
from export_map_layouts import entries
from export_mcall_clips import parse

ROOT=Path(__file__).resolve().parents[1]


def main():
    resources=dict(entries(ROOT/'Meff.e5'))
    rows=[dict(entry=i,**parse(raw)) for i,raw in resources.items()]
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(payload){
  const b=Process.mainModule.base;let selected=null;
  const stop=new NativeCallback(()=>{},'void',['pointer'],'fastcall');
  const sound=new NativeCallback((_obj,id,_loop)=>{selected=id;},'void',
    ['pointer','int','int'],'thiscall');
  Interceptor.replace(b.add(0x74652),stop);Interceptor.replace(b.add(0x7467a),sound);Interceptor.flush();
  const parse=new NativeFunction(b.add(0x1000),'uint',['pointer','pointer'],'thiscall');
  const trigger=new NativeFunction(b.add(0x31e8),'uint',['pointer','uint8'],'thiscall');
  const play=new NativeFunction(b.add(0x205e),'void',['pointer'],'fastcall');
  return payload.map(bytes=>{
    const src=Memory.alloc(bytes.length);src.writeByteArray(bytes);
    const obj=Memory.alloc(0x298);obj.writeByteArray(new Uint8Array(0x298));
    const row={size:parse(obj,src)};
    for(const [name,count,offset] of [['event_offsets',bytes[0],20],['image_offsets',bytes[1],180],
        ['mask_offsets',bytes[2],340],['palette_offsets',bytes[3],500]]){
      row[name]=[];
      for(let i=0;i<count;i++)row[name].push(obj.add(offset+i*4).readPointer().sub(src).toInt32());
    }
    row.triggers=[];
    for(let i=0;i<bytes[0];i++)row.triggers.push(trigger(obj,i)!==0);
    selected=null;play(obj);row.sound=selected;return row;
  });
}};
''')
        script.load();native=script.exports_sync.verify([list(raw) for raw in resources.values()])
        for row,actual in zip(rows,native):
            row['sound_id']=100+(row['extra'] & 255)
            row['sound_file']=f'Se_m_{row["extra"] & 255:02d}.wav'
            triggers=[(i==0 and e['control']!=2) or e['control']==3 for i,e in enumerate(row['timeline'])]
            row['native_match']=(all(row[k]==actual[k] for k in
                ['size','event_offsets','image_offsets','mask_offsets','palette_offsets']) and
                actual['triggers']==triggers and actual['sound']==row['sound_id'] and
                (ROOT/row['sound_file']).is_file())
        (ROOT/'analysis/meff-layouts.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Meff native layouts/audio: {sum(r["native_match"] for r in rows)}/{len(rows)}; '
              f'{sum(r["events"] for r in rows)} timeline records')
        if len(rows)!=58 or not all(r['native_match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
