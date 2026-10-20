"""Validate native stock query/decrement and item-to-stock indexing."""
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(){
 const b=Process.mainModule.base,obj=Memory.alloc(0x500),rows=[];
 const query=new NativeFunction(b.add(0xdb3e),'uint8',['pointer','uint8'],'thiscall');
 const decrement=new NativeFunction(b.add(0xd955),'void',['pointer','uint8'],'thiscall');
 for(let id=0;id<256;id++)for(const count of [0,1,2,254,255]){
  obj.writeByteArray(new Uint8Array(0x500));if(id>=87)obj.add(0x26b+id-87).writeU8(count);
  const before=query(obj,id);decrement(obj,id);const after=query(obj,id);
  rows.push({id,count,before,after});
 }
 return rows;
}};
''');script.load();rows=script.exports_sync.capture()
    for row in rows:row['match']=row['before']==(255 if row['id']<87 else row['count']) and row['after']==(255 if row['id']<87 else max(0,row['count']-1))
    result=dict(total=len(rows),passed=sum(row['match'] for row in rows),rows=rows,scope='native 0x40DB3E/0x40D955/0x40D9C4; isolated stock object; IDs above shipped catalog test arithmetic only')
    text=json.dumps(result,indent=2)+'\n'
    (ROOT/'analysis/native-consumable-inventory.json').write_text(text,encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-consumable-inventory.json').write_text(text,encoding='utf-8')
    print(f'Native consumable inventory: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(row for row in rows if not row['match']))
finally:
    device.kill(pid)
    if session:session.detach()
