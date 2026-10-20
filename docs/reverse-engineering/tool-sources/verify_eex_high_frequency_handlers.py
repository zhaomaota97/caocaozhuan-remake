"""Verify parameter/failure boundaries of EEX handlers 9 and 52."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();lab=ROOT/'analysis/runtime-game';pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base,keep=[];let mode=0,calls=[];
 const reader=new NativeCallback((_obj,tag)=>{if(mode===0)return tag===4?0x80000000:0x8000;if(tag===2)return 0x12; if(tag===13)return 0xfff1; return 0x34;},'uint',['pointer','uint'],'thiscall');keep.push(reader);Interceptor.replace(b.add(0x183f7),reader);
 const effect9=new NativeCallback(value=>{calls.push({target:'0x42c522',value});},'void',['uint'],'mscdecl');keep.push(effect9);Interceptor.replace(b.add(0x2c522),effect9);
 const effect52=new NativeCallback((_a,_b,_c)=>{calls.push({target:'0x428b87',a:_a,b:_b,c:_c});},'void',['uint','int','int'],'mscdecl');keep.push(effect52);Interceptor.replace(b.add(0x28b87),effect52);
 const h9=new NativeFunction(b.add(0x15b0f),'uint',['pointer'],'mscdecl');const h52=new NativeFunction(b.add(0x13567),'uint',['pointer'],'mscdecl');const h51=new NativeFunction(b.add(0x134c9),'uint',['pointer'],'mscdecl');const obj=Memory.alloc(0x40),rows=[];
 for(const value of [0,1]){mode=value;calls=[];rows.push({opcode:9,mode,ret:h9(obj),calls:[...calls]});mode=value;calls=[];rows.push({opcode:52,mode,ret:h52(obj),calls:[...calls]});mode=value;calls=[];rows.push({opcode:51,mode,ret:h51(obj),calls:[...calls]});}
 return rows;
}};''');script.load();result=script.exports_sync.verify()
 out={'rows':result,'passed':result[0]['ret']==5 and result[0]['calls']==[] and result[1]['ret']==5 and result[1]['calls']==[] and result[2]['ret']==5 and result[2]['calls']==[] and result[3]['ret']==1 and result[3]['calls'][0]['target']=='0x42c522' and result[4]['ret']==1 and result[4]['calls'][0]['target']=='0x428b87' and result[5]['ret']==1 and result[5]['calls'][0]['target']=='0x428b87','opcode52ReaderBoundary':'verified: low-16-bit 0x8000 sentinel reaches status-5 branch'}
 (ROOT/'analysis/native-eex-high-frequency-validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
 if not out['passed']:raise SystemExit(1)
finally:
 device.kill(pid)
 if session:
  try:session.detach()
  except frida.InvalidOperationError:pass
