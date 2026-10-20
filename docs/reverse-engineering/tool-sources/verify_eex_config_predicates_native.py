"""Verify EEX opcodes 66/67 interpreter-slot predicates in native code."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();lab=ROOT/'analysis/runtime-game';pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base,keep=[];let refresh5=0,refresh6=0;
 const r5=new NativeCallback(()=>{refresh5++;},'uint',['pointer'],'fastcall');keep.push(r5);Interceptor.replace(b.add(0x4c658),r5);
 const r6=new NativeCallback(()=>{refresh6++;},'uint',['pointer'],'fastcall');keep.push(r6);Interceptor.replace(b.add(0x4c74d),r6);
 const h5=new NativeFunction(b.add(0x11d63),'uint',['pointer'],'mscdecl');const h6=new NativeFunction(b.add(0x11d8e),'uint',['pointer'],'mscdecl');
 const obj=Memory.alloc(0x40),slots=Memory.alloc(7*4),valueMem=Memory.alloc(4);obj.writeByteArray(new Uint8Array(0x40));obj.add(1).writeU8(1);obj.add(0x1c).writePointer(slots);slots.add(5*4).writePointer(valueMem);slots.add(6*4).writePointer(valueMem);const rows=[];
 for(const value of [0,1,2,0xffffffff]){valueMem.writeU32(value);refresh5=0;refresh6=0;const op66=h5(obj),op67=h6(obj);rows.push({opcode:66,value,op66,op67,refresh5,refresh6});rows.push({opcode:67,value,op66,op67,refresh5,refresh6});}
 return rows;
}};''');script.load();result=script.exports_sync.verify()
 out={'rows':result,'passed':all(x['op66']==int(x['value']==1) and x['op67']==int(x['value']==1) and x['refresh5']==1 and x['refresh6']==1 for x in result)}
 (ROOT/'analysis/native-eex-config-predicate-validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
 if not out['passed']:raise SystemExit(1)
finally:
 device.kill(pid)
 if session:
  try:session.detach()
  except frida.InvalidOperationError:pass
