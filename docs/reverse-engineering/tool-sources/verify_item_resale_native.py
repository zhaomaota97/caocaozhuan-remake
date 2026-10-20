"""Read original item price metadata and execute native resale getter."""
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(bytes){
 const b=Process.mainModule.base,p=Memory.alloc(bytes.length);p.writeByteArray(bytes);
 const load=new NativeFunction(b.add(0xc537),'pointer',['pointer','pointer'],'thiscall');
 const resale=new NativeFunction(b.add(0xc7a9),'uint',['pointer','uint'],'thiscall');
 const definitions=[],rows=[];
 for(let id=0;id<104;id++){
  const item=b.add(0xa1140+id*25);load(item,p.add(id*25));
  definitions.push({id,categoryByte:item.add(17).readU8(),priceByte:item.add(18).readU8()});
  for(const level of [0,1,2,3,9,255])rows.push({id,level,value:resale(item,level)});
 }
 return {definitions,rows};
}};
''');script.load();result=script.exports_sync.capture(list(dict(entries(ROOT/'Data.e5'))[1]))
    for row in result['rows']:
        item=result['definitions'][row['id']]
        expected=65535 if item['priceByte']==255 else item['priceByte']*75
        if item['priceByte']!=255 and item['categoryByte']<18:expected=expected*(row['level']+1)//2
        row['match']=row['value']==expected
    result.update(total=len(result['rows']),passed=sum(row['match'] for row in result['rows']),scope='native 0x40C537 loader and 0x40C7A9 resale getter; all 104 original items; no UI or purchase transaction')
    text=json.dumps(result,indent=2)+'\n'
    (ROOT/'analysis/native-item-resale.json').write_text(text,encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-item-resale.json').write_text(text,encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/data/rules/native-item-prices.json').write_text(json.dumps(result['definitions'],indent=2)+'\n',encoding='utf-8')
    print(f'Native item resale: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(row for row in result['rows'] if not row['match']))
finally:
    device.kill(pid)
    if session:session.detach()
