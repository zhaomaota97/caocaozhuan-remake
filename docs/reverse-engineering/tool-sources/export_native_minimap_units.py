"""Capture actual 0x44A436 rectangle calls while replacing only graphics output."""
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT.parent/'caocaozhuan-remake'
raw=(ROOT/'Sv08s.e5s').read_bytes()
device=frida.get_local_device()
pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'))
session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(actors){
 const b=Process.mainModule.base;let color=0;const rectangles=[];
 const noContext=new NativeCallback(()=>{},'void',['int'],'mscdecl');
 const pen=new NativeCallback((_mode,index)=>{color=index;},'void',['uint','uint','uint'],'mscdecl');
 const rectangle=new NativeCallback((left,top,right,bottom,mode)=>{rectangles.push({left,top,right,bottom,mode,colorIndex:color});},'void',['int','int','int','int','int'],'mscdecl');
 Interceptor.replace(b.add(0x7cae3),noContext);
 Interceptor.replace(b.add(0x7d1ca),noContext);
 Interceptor.replace(b.add(0x7d1f1),pen);
 Interceptor.replace(b.add(0x7dbc3),rectangle);Interceptor.flush();
 const input=Memory.alloc(actors.length);input.writeByteArray(actors);
 const load=new NativeFunction(b.add(0x42e26),'pointer',['pointer','pointer'],'thiscall');
 for(let i=0;i<115;i++)load(b.add(0xb2c50+i*36),input.add(i*26));
 b.add(0xb3d08+0x508).writeU8(0);b.add(0xb3d08+0x509).writeU8(0);
 new NativeFunction(b.add(0x4a436),'void',['pointer'],'fastcall')(b.add(0xb3d08));
 return rectangles;
}};
''')
    script.load()
    actual=script.exports_sync.capture(list(raw[1301:4291]))
    expected=[]
    for i in range(115):
        actor=raw[1301+i*26:1301+(i+1)*26]
        if actor[14]!=2: continue
        x,y=actor[8:10]
        color=[42,173,172,172][actor[7] if actor[7]<4 else 0]
        expected.append({'left':x*6,'top':y*6,'right':x*6+4,'bottom':y*6+4,'mode':0,'colorIndex':color})
    if actual!=expected: raise ValueError('Native minimap rectangles differ from reconstructed actor positions/colors')
    palette=dict(entries(ROOT/'Spalet.e5'))[31].ljust(768,b'\0')
    for rect in actual:
        offset=rect['colorIndex']*3
        rgb=[palette[offset+1]&240,palette[offset+2]&240,palette[offset]&240]
        rect['rgb']=rgb
    result={'scope':'Native rectangle output; screen/context/pen/blit sinks replaced','matched':len(actual),'rectangles':actual}
    (ROOT/'analysis/native-slot08-minimap-units.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    (DEST/'data/mappings/minimap-31-units.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(f'Native minimap rectangles: {len(actual)}/{len(expected)} exact position, size and palette-index matches')
finally:
    device.kill(pid)
    if session: session.detach()
