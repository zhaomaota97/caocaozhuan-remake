"""Capture native saved-unit blits and composite them over reconstructed maps."""
import json
from pathlib import Path
from PIL import Image
import frida
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]


def main():
    data=dict(entries(ROOT/'Data.e5'));mov=dict(entries(ROOT/'Unit_mov.e5'))
    palettes=dict(entries(ROOT/'Spalet.e5'))
    layouts=json.loads((ROOT/'analysis/map-layouts/layouts.json').read_text())['hexzmap']
    dimensions={r['id']:(r['width'],r['height']) for r in layouts}
    saves=[]
    for path in sorted(ROOT.glob('Sv??s.e5s')):
        raw=path.read_bytes();map_id=raw[35];width,height=dimensions[map_id]
        saves.append(dict(file=path.name,width=width,height=height,
            state=list(raw[35:1301]),actors=list(raw[1301:4291]),
            roster=list(path.with_name(path.name.replace('s.e5s','d.e5s')).read_bytes()[0x14dc:]),
            terrain=list((ROOT/f'analysis/saved-battlefields/{path.stem}-terrain.bin').read_bytes()),
            palette=list(palettes[map_id].ljust(768,b'\0'))))
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={render(source,items,mov,mark,saves){
  const b=Process.mainModule.base;let blits=[];
  const capture=new NativeCallback((x,y,w,h,pixels,_mode)=>{
    blits.push({x:x.toInt32(),y:y.toInt32(),width:w,height:h,
      pixels:Array.from(new Uint8Array(pixels.readByteArray(w*h)))});
  },'void',['pointer','pointer','uint','int','pointer','uint'],'mscdecl');
  Interceptor.replace(b.add(0x51913),capture);Interceptor.flush();
  const expand=new NativeFunction(b.add(0x8be3),'pointer',['pointer','uint16','pointer','int'],'thiscall');
  const loadItem=new NativeFunction(b.add(0xc537),'pointer',['pointer','pointer'],'thiscall');
  const loadUnit=new NativeFunction(b.add(0x9188),'pointer',['pointer','pointer'],'thiscall');
  const loadActor=new NativeFunction(b.add(0x42e26),'pointer',['pointer','pointer'],'thiscall');
  const loadState=new NativeFunction(b.add(0x4f384),'pointer',['pointer','pointer'],'thiscall');
  const sprite=new NativeFunction(b.add(0x3fc48),'uint',['pointer'],'fastcall');
  const mirror=new NativeFunction(b.add(0x3fd34),'void',['pointer','int'],'thiscall');
  const paletteLut=new NativeFunction(b.add(0x2fcc6),'void',['pointer'],'mscdecl');
  const draw=new NativeFunction(b.add(0x3eb1f),'void',['pointer','pointer','int'],'mscdecl');
  const drawMarker=new NativeFunction(b.add(0x52744),'void',['pointer','pointer','uint8'],'mscdecl');
  function buffer(bytes){const p=Memory.alloc(bytes.length);p.writeByteArray(bytes);return p;}
  function view(rva,length){
    const p=Memory.alloc(length);p.writeByteArray(new Uint8Array(length));
    const v=b.add(rva);v.add(4).writeU32(length);v.add(12).writePointer(p);v.add(16).writeU8(1);return p;
  }
  const original=buffer(source),itemData=buffer(items);
  for(let i=0;i<512;i++)expand(b.add(0xa1b68+i*72),i,original.add(i*32),0);
  for(let i=0;i<104;i++)loadItem(b.add(0xa1140+i*25),itemData.add(i*25));
  const pool=view(0xaab80,115*25344),scratch=view(0xaf490,0x5000);
  const marks=view(0xaeb50,mark.length);marks.writeByteArray(mark);
  const map=view(0xaeb38,9600),results=[];
  for(const save of saves){
    const roster=buffer(save.roster),actors=buffer(save.actors),state=buffer(save.state);
    for(let i=0;i<512;i++)loadUnit(b.add(0xa1b68+i*72),roster.add(i*32));
    loadState(b.add(0xb3d08),state);
    b.add(0xb422c).writeU8(save.width);b.add(0xb422d).writeU8(save.height);
    map.add(0x640).writeByteArray(save.terrain);
    b.add(0x97770).writeByteArray(save.palette.map(v=>v>>4));paletteLut(b.add(0x97770));
    const visible=[],skipped=[];
    for(let i=0;i<115;i++){
      const actor=b.add(0xb2c50+i*36);loadActor(actor,actors.add(i*26));
      if(actor.add(12).readU8()!==2)continue;
      const uid=actor.readU32(),cache=actor.add(4).readU8();
      const x=actor.add(6).readU8(),y=actor.add(7).readU8();
      if(uid>=512||cache>=115||x>=save.width||y>=save.height){skipped.push(i);continue;}
      const index=sprite(actor)&255;
      pool.add(cache*25344).writeByteArray(mov[index]);
      const flags=actor.add(13).readU8();actor.add(13).writeU8(flags&~8);
      mirror(actor,(flags&8)!==0?1:0);
      visible.push({slot:i,uid,index,x,y});
    }
    blits=[];
    const markers=new Map();
    for(let i=0;i<250;i++){
      const off=16+i*5,kind=save.state[off+4];
      if(kind<4)markers.set(save.state[off]+save.state[off+1]*save.width,kind);
    }
    const markerRecords=[];
    for(const [pos,kind] of markers){
      const x=pos%save.width,y=Math.floor(pos/save.width);
      drawMarker(ptr(x*48),ptr(y*48),kind);markerRecords.push({x,y,kind});
    }
    visible.sort((a,c)=>a.y-c.y||a.x-c.x);
    for(const unit of visible)draw(ptr(unit.x*48),ptr(unit.y*48),unit.slot);
    results.push({file:save.file,units:visible,skipped,markers:markerRecords,blits});
  }
  return results;
}};
''')
        script.load()
        results=script.exports_sync.render(list(data[0]),list(data[1]),
            {str(i):list(raw) for i,raw in mov.items()},list((ROOT/'Mark.e5').read_bytes()),saves)
        output=ROOT/'analysis/saved-unit-scenes';output.mkdir(exist_ok=True)
        mark=(ROOT/'Mark.e5').read_bytes()
        for result in results:
            stem=Path(result['file']).stem
            image=Image.open(ROOT/f'analysis/saved-battlefields/{stem}-gates.png').copy()
            phase=next(save['state'][11] for save in saves if save['file']==result['file'])
            for record,blit in zip(result['markers'],result['blits']):
                offset=[0x8bc0+(phase&3)*2304,0xafc0+(phase&1)*2304,
                        0x1b5e0+(phase&1)*2304,0x1ec0][record['kind']]
                if bytes(blit['pixels'])!=mark[offset:offset+2304]:
                    raise ValueError('Native marker frame does not match expected Mark resource')
            result['marker_frames_verified']=len(result['markers'])
            for blit in result['blits']:
                pixels=bytes(blit['pixels']);size=(blit['width'],blit['height'])
                tile=Image.frombytes('P',size,pixels)
                mask=Image.frombytes('L',size,bytes(255 if p else 0 for p in pixels))
                image.paste(tile,(blit['x'],blit['y']),mask)
            image.save(output/f'{stem}-units.png')
            result['blit_count']=len(result.pop('blits'))
        (output/'manifest.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        print(f'Reconstructed {len(results)} saved scenes with '
              f'{sum(len(r["units"]) for r in results)} native-rendered units; '
              f'{sum(len(r["skipped"]) for r in results)} skipped')
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
