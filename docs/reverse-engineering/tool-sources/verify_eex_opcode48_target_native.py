"""Verify native opcode-48 target key resolution and fixed dispatch arguments."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();lab=ROOT/'analysis/runtime-game';pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base,keep=[],calls=[];
 const target=new NativeCallback((a,c,d,e,f,g,h,i,j)=>{calls.push([a,c,d,e,f,g,h,i,j]);},'void',['int','int','int','int','int','int','int','int','int'],'mscdecl');keep.push(target);Interceptor.replace(b.add(0x28eb0),target);
 const run=new NativeFunction(b.add(0x2909d),'uint',['uint16','uint16','uint16','uint16','uint16','uint16'],'mscdecl');
 const entry=b.add(0x9cf68+7*0x40);entry.writeByteArray(new Uint8Array(0x40));entry.add(0x28).writeU16(0x8000);entry.add(0x3a).writeU16(0x2345);
 const ret=run(0x1345,0x21,0x22,0x23,0x24,0x99);return {ret,calls};
}};''');script.load();result=script.exports_sync.verify()
 out={'result':result,'passed':result['ret']==0xffff and len(result['calls'])==1 and result['calls'][0][0]==0x1345 and result['calls'][0][4:7]==[3,3,1], 'abiNote':'short arguments are packed/sign-extended under the native call ABI; only the namespace and fixed mode fields are asserted'}
 (ROOT/'analysis/native-eex-opcode48-target-validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
 if not out['passed']:raise SystemExit(1)
finally:
 device.kill(pid)
 if session:
  try:session.detach()
  except frida.InvalidOperationError:pass
