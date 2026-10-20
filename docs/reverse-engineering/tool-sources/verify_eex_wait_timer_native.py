"""Execute native wait target using a deterministic clock and message pump."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device()
pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'))
session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base;let tick=1000,pumps=0;
 const clock=new NativeCallback(()=>tick,'uint',[],'mscdecl');
 const pump=new NativeCallback(()=>{tick++;pumps++;},'void',[],'mscdecl');
 Interceptor.replace(b.add(0x7eb97),clock);Interceptor.replace(b.add(0x7eac4),pump);Interceptor.flush();
 const wait=new NativeFunction(b.add(0x2c522),'void',['int'],'mscdecl'),rows=[];
 for(const value of [0,1,2,10,100]){
  tick=1000;pumps=0;b.add(0xb1b18).writeU32(777);wait(value);
  rows.push({value,tick,pumps,deadline:b.add(0xb1b18).readU32()});
 }
 return rows;
}};''')
 script.load();rows=script.exports_sync.verify()
 for row in rows:
  row['match']=(row['pumps']==row['value']*2 and row['tick']==1000+row['value']*2
                and row['deadline']==(1000+row['value']*2 if row['value'] else 777))
 out={'scope':'Native timer controller; clock and message pump controlled','rows':rows,'passed':all(row['match'] for row in rows)}
 (ROOT/'analysis/native-eex-wait-timer-validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print(f"Native opcode-9 wait timer: {sum(row['match'] for row in rows)}/{len(rows)}")
 if not out['passed']:raise SystemExit(1)
finally:
 device.kill(pid)
 if session:session.detach()
