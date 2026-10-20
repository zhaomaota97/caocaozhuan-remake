"""Probe native consumable amount helper with controlled maximum getters."""
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(){
 const b=Process.mainModule.base,actor=Memory.alloc(36),item=b.add(0xa1140),keep=[];let maximum=100;
 for(const rva of [0x721b,0x724a]){const cb=new NativeCallback(()=>maximum,'uint',['pointer','uint'],'fastcall');keep.push(cb);Interceptor.replace(b.add(rva),cb);}Interceptor.flush();
 actor.writeByteArray(new Uint8Array(36));item.writeByteArray(new Uint8Array(25));
 const amount=new NativeFunction(b.add(0x3c42e),'uint',['pointer','uint'],'thiscall'),rows=[];
 for(const category of [63,64,70])for(const value of [0,1,30,254,255])for(const max of [100,250,500])for(const current of [0,1,99,max]){
  maximum=max;actor.add(16).writeU32(current);actor.add(20).writeU32(current);item.add(17).writeU8(category);item.add(21).writeU8(value);
  rows.push({category,value,maximum,current,amount:amount(actor,0)});
 }
 return rows;
}};
''');script.load();rows=script.exports_sync.capture()
    for row in rows:
        gap=row['maximum']-row['current']
        expected=(gap if row['value']==255 else min(row['value'],gap)) if row['category'] in (63,64) else row['value']
        row['match']=row['amount']==expected
    result=dict(total=len(rows),passed=sum(row['match'] for row in rows),rows=rows,scope='native 0x43C42E; max HP/MP getters controlled; current within max; no inventory or presentation')
    text=json.dumps(result,indent=2)+'\n'
    (ROOT/'analysis/native-item-restore-amount.json').write_text(text,encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-item-restore-amount.json').write_text(text,encoding='utf-8')
    print(f'Native item restore amount: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(row for row in rows if not row['match']))
finally:
    device.kill(pid)
    if session:session.detach()
