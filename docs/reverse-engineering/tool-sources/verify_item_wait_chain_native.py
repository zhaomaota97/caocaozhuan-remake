"""Execute the exact timer entry points used in native item presentation."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(){
 const b=Process.mainModule.base;let tick=1000,pumps=0;
 const clock=new NativeCallback(()=>tick,'uint',[],'mscdecl');
 const pump=new NativeCallback(()=>{tick++;pumps++;},'void',[],'mscdecl');
 Interceptor.replace(b.add(0x7eb97),clock);Interceptor.replace(b.add(0x7eac4),pump);Interceptor.flush();
 const set=new NativeFunction(b.add(0x3340),'void',['pointer','int'],'thiscall');
 const wait=new NativeFunction(b.add(0x2c4e0),'void',[],'mscdecl'),rows=[];
 for(const amount of [0,1,5,10,255])for(const elapsed of [0,1,3,10]){
  tick=1000;pumps=0;set(b.add(0xb1b18),amount);tick+=elapsed;wait();
  rows.push({amount,elapsed,tick,pumps,deadline:b.add(0xb1b18).readU32()});
 }
 return rows;
}};
''');script.load();rows=script.exports_sync.capture()
    for r in rows:r['match']=r['pumps']==max(0,r['amount']-r['elapsed']) and r['deadline']==1000+r['amount'] and r['tick']==1000+max(r['amount'],r['elapsed'])
    result=dict(total=len(rows),passed=sum(r['match'] for r in rows),rows=rows,scope='native 0x403340 -> 0x42C45F and 0x42C4E0 deadline loop; clock/message pump controlled, not real-time rendering')
    text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/native-item-wait-chain.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-item-wait-chain.json').write_text(text,encoding='utf-8')
    print(f'Native item wait chain: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(r for r in rows if not r['match']))
finally:
    device.kill(pid)
    if session:session.detach()
