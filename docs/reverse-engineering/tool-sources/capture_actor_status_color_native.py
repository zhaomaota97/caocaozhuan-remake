"""Capture native actor status-color conversion and darkening composition."""
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
 const dark=new NativeFunction(b.add(0x30480),'void',['pointer','int','int','uint8'],'mscdecl');
 const status=new NativeFunction(b.add(0x3053e),'void',['pointer','int','int','uint8','uint8','uint8'],'mscdecl');
 return cases.map(row=>{b.add(0x97770).writeByteArray(row.palette);build(b.add(0x97770));const rows=[];
  for(const acted of [false,true]){pixels.writeByteArray(Array.from({length:256},(_,i)=>i));if(acted)dark(pixels,256,1,4);status(pixels,256,1,4,8,4);rows.push({acted,pixels:Array.from(new Uint8Array(pixels.readByteArray(256)))});}
  return {...row,rows};
 });
}};
''');script.load();rows=script.exports_sync.capture(cases)
    result=dict(pixels=1536,rows=rows,scope='unmodified 0x43053E with renderer arguments4/8/4 after optional original 0x430480; original lookup generation; zero-tail supplied palettes; not full renderer or gate execution')
    text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/native-actor-status-color.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-actor-status-color.json').write_text(text,encoding='utf-8')
    print('Native actor status color: 1536 pixels captured including darkening composition')
finally:
    device.kill(pid)
    if session:session.detach()
