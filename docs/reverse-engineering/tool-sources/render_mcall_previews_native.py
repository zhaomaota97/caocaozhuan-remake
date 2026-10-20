"""Render clip previews on a real reconstructed scene using original pixel mixers."""
import json
import threading
from pathlib import Path
from PIL import Image
import frida
from export_map_layouts import entries
from export_mcall_clips import parse

ROOT=Path(__file__).resolve().parents[1]


def main():
    base=Image.open(ROOT/'analysis/saved-unit-scenes/Sv00s-units.png').copy()
    current=bytes(v>>4 for v in dict(entries(ROOT/'Spalet.e5'))[0])
    output=ROOT/'analysis/mcall-previews';output.mkdir(exist_ok=True)
    received=[];ready=threading.Event();expected_count=0
    def message(item,data):
        if item['type']=='send' and item['payload'].get('event')=='frame':
            received.append((item['payload']['index'],bytes(data)))
            if len(received)==expected_count:ready.set()
        elif item['type']=='error':
            print(item.get('stack',item))
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={render(raw,current,layout,backgrounds){
  const b=Process.mainModule.base;
  function alloc(bytes){const p=Memory.alloc(bytes.length);p.writeByteArray(bytes);return p;}
  const clip=alloc(raw),out=Memory.alloc(layout.width*layout.height);
  b.add(0x97770).writeByteArray(current);
  const build=new NativeFunction(b.add(0x2fcc6),'void',['pointer'],'mscdecl');build(b.add(0x97770));
  const masked=new NativeFunction(b.add(0x300c8),'void',
    ['int','int','pointer','pointer','pointer','pointer','pointer','uint8'],'mscdecl');
  const constant=new NativeFunction(b.add(0x2fd5a),'void',
    ['int','int','pointer','pointer','pointer','uint8','int','pointer','uint8'],'mscdecl');
  const keyed=new NativeFunction(b.add(0x7f740),'void',
    ['int','int','int','int','pointer','pointer','int'],'mscdecl');
  for(let i=0;i<layout.events;i++){
    const e=layout.timeline[i],src=clip.add(layout.image_offsets[e.image]);
    const bg=alloc(backgrounds[i]);
    const palette=e.palette===255?ptr(0):clip.add(layout.palette_offsets[e.palette]);
    if(e.mask_mode!==0){
      const mask=clip.add(layout.mask_offsets[e.mask_or_blend]);
      masked(layout.width,layout.height,src,mask,bg,out,palette,e.strength);
    }else if(e.mask_or_blend===0 && palette.isNull()){
      out.writeByteArray(backgrounds[i]);
      keyed(layout.width,layout.height,layout.width,layout.width,src,out,7);
    }else constant(layout.width,layout.height,src,bg,out,e.mask_or_blend,0,palette,e.strength);
    send({event:'frame',index:i},out.readByteArray(layout.width*layout.height));
  }
  return layout.events;
}};
''')
        script.on('message',message);script.load();manifest=[]
        for path in sorted(ROOT.glob('Mcall??.e5')):
            raw=path.read_bytes();layout=parse(raw);width,height=layout['width'],layout['height']
            positions=[((base.width-width)//2+e['x'],(base.height-height)//2+e['y']) for e in layout['timeline']]
            backgrounds=[list(base.crop((x,y,x+width,y+height)).tobytes()) for x,y in positions]
            received.clear();ready.clear();expected_count=layout['events']
            count=script.exports_sync.render(list(raw),list(current),layout,backgrounds)
            if not ready.wait(10) or len(received)!=count:raise RuntimeError('Missing native frame data')
            frames=[]
            for (index,pixels),(x,y) in zip(sorted(received),positions):
                tile=Image.frombytes('P',(width,height),pixels)
                image=base.copy();image.paste(tile,(x,y))
                frames.append(image.resize((480,480),Image.Resampling.NEAREST))
            if len(frames)!=layout['events']:raise ValueError('Frame count mismatch')
            gif=output/f'{path.stem}.gif'
            nominal_duration=(layout['interval']//50)*50
            frames[0].save(gif,save_all=True,append_images=frames[1:],duration=nominal_duration,
                           loop=0,optimize=False,disposal=1)
            frames[len(frames)//2].save(output/f'{path.stem}-middle.png')
            manifest.append(dict(file=path.name,frames=len(frames),preview=gif.name,
                native_pixel_mixers=True,preview_duration_ms=nominal_duration,
                original_scheduler_reproduced=False,background='Sv00s-units.png'))
            print(f'{path.name}: {len(frames)} native-mixed frames',flush=True)
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
