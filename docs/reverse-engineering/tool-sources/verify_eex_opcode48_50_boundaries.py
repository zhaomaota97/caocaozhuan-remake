"""Verify missing-parameter boundaries for high-frequency EEX opcodes 48/50."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();lab=ROOT/'analysis/runtime-game';pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base,keep=[];let missingIndex=0,reads=[];
 const reader=new NativeCallback((_obj,tag)=>{const index=reads.length;reads.push(tag);if(index===missingIndex)return tag===4?0x80000000:0x8000;return 1;},'uint',['pointer','uint'],'thiscall');keep.push(reader);Interceptor.replace(b.add(0x183f7),reader);Interceptor.flush();
 const h48=new NativeFunction(b.add(0x13010),'uint',['pointer'],'mscdecl');const h50=new NativeFunction(b.add(0x132d4),'uint',['pointer'],'mscdecl');const obj=Memory.alloc(0x40),rows=[];
 for(const [opcode,handler,tags] of [[48,h48,[2,4,4,43,13]],[50,h50,[64,2,4,4,4,43]]]){
  for(let i=0;i<tags.length;i++){missingIndex=i;reads=[];const ret=handler(obj);rows.push({opcode,missingIndex:i,expectedReads:tags.slice(0,i+1),reads:[...reads],ret});}
 }
 return rows;
}};''');script.load();result=script.exports_sync.verify()
 out={'scope':'Native handler early-return boundaries; reader replaced; no success-path effects tested','rows':result,'passed':len(result)==11 and all(x['ret']==5 and x['reads']==x['expectedReads'] for x in result)}
 (ROOT/'analysis/native-eex-48-50-boundary-validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
 if not out['passed']:raise SystemExit(1)
finally:
 device.kill(pid)
 if session:
  try:session.detach()
  except frida.InvalidOperationError:pass
