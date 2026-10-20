"""Verify EEX conditional handlers 14, 73 and 84 with native condition branches."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();lab=ROOT/'analysis/runtime-game';pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base,keep=[];
 let condition=0, calls=[];
 const cond=new NativeCallback(()=>condition,'uint8',[],'mscdecl');keep.push(cond);Interceptor.replace(b.add(0xb922),cond);
 const action=new NativeCallback((_self,value)=>{calls.push(value);},'void',['pointer','int'],'thiscall');keep.push(action);Interceptor.replace(b.add(0x55ffd),action);
 const action84=new NativeCallback(()=>{calls.push(0x4cc03);},'void',[],'mscdecl');keep.push(action84);Interceptor.replace(b.add(0x4cc03),action84);
 const h14=new NativeFunction(b.add(0x15890),'uint',[],'mscdecl');
 const h73=new NativeFunction(b.add(0x15795),'uint',[],'mscdecl');
 const h84=new NativeFunction(b.add(0x15771),'uint',[],'mscdecl');
 const rows=[];for(const value of [0,1]){condition=value;calls=[];rows.push({opcode:14,condition:value,ret:h14(),calls:[...calls]});condition=value;calls=[];rows.push({opcode:73,condition:value,ret:h73(),calls:[...calls]});condition=value;calls=[];rows.push({opcode:84,condition:value,ret:h84(),calls:[...calls]});}
 return rows;
}};''');script.load();result=script.exports_sync.verify()
 out={'rows':result,'passed':all(r['ret']==1 and r['calls']==([] if r['condition']==0 else ([3] if r['opcode']==14 else [2] if r['opcode']==73 else [0x4cc03])) for r in result)}
 (ROOT/'analysis/native-eex-conditional-validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
 if not out['passed']:raise SystemExit(1)
finally:
 device.kill(pid)
 if session:
  try:session.detach()
  except frida.InvalidOperationError:pass
