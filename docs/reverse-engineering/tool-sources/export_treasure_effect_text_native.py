"""Export treasure effect labels using original native UI formatters."""
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]
path=ROOT.parent/'caocaozhuan-remake/data/mappings/treasure-catalog.json'
catalog=json.loads(path.read_text(encoding='utf-8'))
device=frida.get_local_device()
pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'))
session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={read(items,ids){
 const b=Process.mainModule.base,input=Memory.alloc(items.length);input.writeByteArray(items);
 const decode=new NativeFunction(b.add(0xc537),'pointer',['pointer','pointer'],'thiscall');
 for(let i=0;i<104;i++)decode(b.add(0xa1140+i*25),input.add(i*25));
 const primary=new NativeFunction(b.add(0x62005),'void',['pointer','pointer','int','uint8'],'thiscall');
 const extra=new NativeFunction(b.add(0x62174),'void',['pointer','int'],'mscdecl');
 const output=Memory.alloc(1024);
 function bytes(){const result=[];for(let i=0;i<1024;i++){const c=output.add(i).readU8();if(!c)return result;result.push(c);}throw new Error('unterminated text');}
 return ids.map(id=>{output.writeByteArray(new Uint8Array(1024));primary(ptr(0),output,id,1);const effect=bytes();output.writeByteArray(new Uint8Array(1024));extra(output,id);return {id,effect,extra:bytes()};});
}};
''')
    script.load()
    result=script.exports_sync.read(list(dict(entries(ROOT/'Data.e5'))[1]),[r['itemId'] for r in catalog['entries']])
    by_id={r['id']:r for r in result}
    for row in catalog['entries']:
        observed=by_id[row['itemId']]
        row['effectText']=bytes(observed['effect']).decode('cp936')
        row['additionalEffectText']=bytes(observed['extra']).decode('cp936')
    path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'analysis/native-treasure-effect-text.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f'Exported native primary/additional effect text for {len(result)} treasures')
finally:
    device.kill(pid)
    if session:
        try:session.detach()
        except frida.InvalidOperationError:pass
