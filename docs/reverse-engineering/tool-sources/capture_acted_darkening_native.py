"""Capture native actor darkening pixel transform with original palette lookup."""
import json
from pathlib import Path
import frida
from export_map_layouts import entries
ROOT=Path(__file__).resolve().parents[1];palettes=dict(entries(ROOT/'Spalet.e5'))
cases=[dict(paletteEntry=index,palette=[v>>4 for v in palettes[index].ljust(768,b'\0')]) for index in [0,31,57]]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(cases){
 const b=Process.mainModule.base,pixels=Memory.alloc(256),build=new NativeFunction(b.add(0x2fcc6),'void',['pointer'],'mscdecl');
 const darken=new NativeFunction(b.add(0x30480),'void',['pointer','int','int','uint8'],'mscdecl');
 return cases.map(row=>{b.add(0x97770).writeByteArray(row.palette);build(b.add(0x97770));const rows=[];
  for(const amount of [0,1,4,15]){pixels.writeByteArray(Array.from({length:256},(_,i)=>i));darken(pixels,256,1,amount);rows.push({amount,pixels:Array.from(new Uint8Array(pixels.readByteArray(256)))});}
  return {...row,rows};
 });
}};
''');script.load();rows=script.exports_sync.capture(cases)
    result=dict(scope='unmodified native 0x430480 plus 0x42FCC6; explicit zero-tail palette; actual acted render uses amount4; not full actor renderer',pixels=3072,rows=rows)
    text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/native-acted-darkening.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-acted-darkening.json').write_text(text,encoding='utf-8')
    print('Native darkening captured: 3072 pixel outputs across three palettes')
finally:
    device.kill(pid)
    if session:session.detach()
