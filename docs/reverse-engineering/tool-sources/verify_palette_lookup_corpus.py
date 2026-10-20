"""Capture unmodified native color lookup builder across every Spalet palette."""
import json
from pathlib import Path
import frida
from export_map_layouts import entries
ROOT=Path(__file__).resolve().parents[1]
cases=[dict(name=f'Spalet:{index}',resourceBytes=len(raw),palette=[value>>4 for value in raw.ljust(768,b'\0')]) for index,raw in entries(ROOT/'Spalet.e5')]
cases.extend([dict(name='synthetic:black',palette=[0]*768),dict(name='synthetic:equal',palette=[7]*768),dict(name='synthetic:channels',palette=[(index//3+index%3*5)%16 for index in range(768)])])
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(cases){
 const b=Process.mainModule.base,p=Memory.alloc(768),build=new NativeFunction(b.add(0x2fcc6),'void',['pointer'],'mscdecl');
 return cases.map(row=>{p.writeByteArray(row.palette);build(p);return {...row,lookup:Array.from(new Uint8Array(b.add(0xb1b28).readByteArray(4096)))};});
}};
''');script.load();rows=script.exports_sync.capture(cases)
    result=dict(total=len(rows),entries=len(rows)*4096,rows=rows,scope='unmodified native 0x42FCC6/0x42FB10; every Spalet resource with explicit zero-padded tail plus synthetic palettes; not preceding live scene palette state')
    text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/native-palette-lookup-corpus.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-palette-lookup-corpus.json').write_text(text,encoding='utf-8')
    print(f'Native palette lookup corpus: {len(rows)} palettes, {result["entries"]} entries captured')
finally:
    device.kill(pid)
    if session:session.detach()
