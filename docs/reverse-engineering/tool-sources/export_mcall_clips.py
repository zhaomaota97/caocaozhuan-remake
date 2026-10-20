"""Parse raw Mcall effect clips and compare native parser pointer boundaries."""
import json
import struct
import csv
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def parse(raw):
    events,images,masks,palettes,interval,width,height,extra=struct.unpack_from('<4B4I',raw)
    pixel_size=width*height
    offset=20
    event_offsets=[offset+i*20 for i in range(events)];offset+=events*20
    image_offsets=[offset+i*pixel_size for i in range(images)];offset+=images*pixel_size
    mask_offsets=[offset+i*pixel_size for i in range(masks)];offset+=masks*pixel_size
    palette_offsets=[offset+i*768 for i in range(palettes)];offset+=palettes*768
    if offset!=len(raw):raise ValueError('Native layout does not reach EOF')
    timeline=[]
    for position in event_offsets:
        image,palette,mask_or_blend,strength,mode,x,y,control,tail=struct.unpack_from('<4BIiiB3s',raw,position)
        if image>=images or (palette!=255 and palette>=palettes) or (mode!=0 and mask_or_blend>=masks):
            raise ValueError('Timeline resource index out of range')
        timeline.append(dict(image=image,palette=palette,mask_or_blend=mask_or_blend,
            strength=strength,mask_mode=mode,x=x,y=y,control=control,opaque_tail=tail.hex()))
    return dict(events=events,images=images,masks=masks,palettes=palettes,
        interval=interval,width=width,height=height,extra=extra,size=offset,
        event_offsets=event_offsets,image_offsets=image_offsets,mask_offsets=mask_offsets,
        palette_offsets=palette_offsets,
        timeline=timeline)


def main():
    files=sorted(ROOT.glob('Mcall??.e5'))
    payload=[list(p.read_bytes()) for p in files]
    records=[dict(file=p.name,**parse(bytes(raw))) for p,raw in zip(files,payload)]
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(payload){
  let selected=null;
  const audio=new NativeCallback((_obj,id,_loop)=>{selected=id;},'void',
    ['pointer','int','int'],'thiscall');
  Interceptor.replace(Process.mainModule.base.add(0x7467a),audio);Interceptor.flush();
  const shouldSound=new NativeFunction(Process.mainModule.base.add(0x3262),'uint',['pointer'],'fastcall');
  const playSound=new NativeFunction(Process.mainModule.base.add(0x3147),'void',['pointer'],'fastcall');
  const parse=new NativeFunction(Process.mainModule.base.add(0x1000),'uint',
    ['pointer','pointer'],'thiscall');
  return payload.map(bytes=>{
    const source=Memory.alloc(bytes.length);source.writeByteArray(bytes);
    const obj=Memory.alloc(0x298);obj.writeByteArray(new Uint8Array(0x298));
    const size=parse(obj,source),row={size};
    for(const [name,count,base] of [['event_offsets',bytes[0],20],['image_offsets',bytes[1],180],
        ['mask_offsets',bytes[2],340],['palette_offsets',bytes[3],500]]){
      row[name]=[];
      for(let i=0;i<count;i++)row[name].push(obj.add(base+i*4).readPointer().sub(source).toInt32());
    }
    row.second_parse=parse(obj,source);
    const stream=Memory.alloc(0x5c);stream.writeByteArray(new Uint8Array(0x5c));
    stream.add(0x2c).writeU8(bytes[16]);row.triggers=[];row.sound_ids=[];
    for(let frame=0;frame<bytes[0];frame++){
      stream.add(0x58).writeU8(frame);stream.add(0x40).writeU8(bytes[20+frame*20+16]);
      const trigger=shouldSound(stream)!==0;selected=null;
      if(trigger)playSound(stream);
      row.triggers.push(trigger);row.sound_ids.push(selected);
    }
    return row;
  });
}};
''')
        script.load();native=script.exports_sync.verify(payload)
        for record,observed in zip(records,native):
            triggers=[(i==0 and event['control']!=2) or event['control']==3
                      for i,event in enumerate(record['timeline'])]
            sound=(record['extra'] & 255)+100
            record['native_sound_match']=(triggers==observed['triggers'] and
                observed['sound_ids']==[sound if triggered else None for triggered in triggers])
            record['native_match']=(all(record[k]==observed[k] for k in
                ['size','event_offsets','image_offsets','mask_offsets','palette_offsets']) and
                observed['second_parse']==0 and record['native_sound_match'])
        (ROOT/'analysis/mcall-layouts.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
        with (ROOT/'analysis/mcall-timeline.csv').open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.writer(f)
            writer.writerow(['file','frame','image','palette','mask_or_blend','strength',
                             'mask_mode','x','y','control','sound_trigger','sound_id','sound_file','opaque_tail'])
            for record in records:
                sound=(record['extra'] & 255)+100
                for frame,event in enumerate(record['timeline']):
                    trigger=(frame==0 and event['control']!=2) or event['control']==3
                    writer.writerow([record['file'],frame,*[event[k] for k in
                        ['image','palette','mask_or_blend','strength','mask_mode','x','y','control']],
                        trigger,sound,f'Se_m_{sound-100:02d}.wav',event['opaque_tail']])
        print(f'Mcall native layouts: {sum(r["native_match"] for r in records)}/{len(records)}; '
              f'{sum(r["events"] for r in records)} timeline records')
        if len(records)!=9 or not all(r['native_match'] for r in records):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
