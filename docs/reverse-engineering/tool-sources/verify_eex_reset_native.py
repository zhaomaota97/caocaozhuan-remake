"""Verify native EEX opcode 68 reset against its global scenario table."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();lab=ROOT/'analysis/runtime-game';pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base;
 let calls=0,firstThis='';
 Interceptor.attach(b.add(0x184d1),{onEnter(args){if(calls++===0)firstThis=this.context.ecx.toString();}});
 const reset=new NativeFunction(b.add(0x12230),'uint',['pointer'],'mscdecl');
 const object=b.add(0xae458),table=object.add(0x38), before=[],after=[],initial=[];
 for(let i=0;i<115;i++)initial.push(b.add(0x8b350+i*4).readU32());
 for(let i=0;i<256;i++)table.add(i*4).writeU32(0xdead0000+i);
 for(let i=0;i<115;i++){let p=b.add(0x92f90+0x2044+i*0x40);p.writeU32(0xabc00000+i);p.add(8).writeU32(0x12340000+i);}
 for(let i=0;i<8;i++)before.push({i,value:b.add(0x92f90+0x2044+i*0x40).readU32(),flags:b.add(0x92f90+0x2044+i*0x40+8).readU32()});
 const ret=reset(object);
 const records=[];for(let i=0;i<115;i++){const p=b.add(0x92f90+0x2044+i*0x40);records.push({value:p.readU32(),flags:p.add(8).readU32()});}
 for(let i=0;i<8;i++)after.push({i,value:b.add(0x92f90+0x2044+i*0x40).readU32(),flags:b.add(0x92f90+0x2044+i*0x40+8).readU32()});
 return {ret,tableFirst:table.readU32(),tableLast:table.add(255*4).readU32(),before,after,records,calls,firstThis,initial};
}};''');script.load();result=script.exports_sync.verify()
 expected=[]
 for value in result['initial']:
  if value == 0xffff: break
  expected.append(value)
 out={'result':result,'passed':result['ret']==1 and result['tableFirst']==0 and result['tableLast']==0 and all(x['flags']==0 for x in result['records']) and [x['value'] for x in result['records'][:len(expected)]]==expected}
 (ROOT/'analysis/native-eex-reset-validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
 if not out['passed']:raise SystemExit(1)
finally:
 device.kill(pid)
 if session:
  try:session.detach()
  except frida.InvalidOperationError:pass
