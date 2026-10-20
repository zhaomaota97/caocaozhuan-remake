"""Execute native handlers with controlled readers and recorded effect leaves."""
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]
source=r'''rpc.exports={verify(){
 const b=Process.mainModule.base,keep=[],rows=[];
 let values=[],reads=[],calls=[],condition=0,scene=0;
 function replace(rva,ret,args,abi,fn){const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);Interceptor.replace(b.add(rva),cb);}
 replace(0x183f7,'uint',['pointer','uint'],'thiscall',(_obj,tag)=>{reads.push(tag);return values[reads.length-1];});
 replace(0xb922,'uint',[],'mscdecl',()=>condition);
 replace(0x18c00,'uint',['pointer'],'fastcall',()=>scene);
 replace(0x2909d,'uint',['uint16','uint16','uint16','uint16','uint16','uint16'],'mscdecl',(...args)=>{calls.push(['effect48',...args]);return 65535;});
 replace(0x570ee,'uint',['int'],'mscdecl',id=>{calls.push(['actor48',id]);return 1;});
 replace(0x29159,'uint',['uint16','uint16','uint16','uint16'],'mscdecl',(...args)=>{calls.push(['effect50',...args]);return 65535;});
 replace(0x59487,'uint',['int','uint8','uint8','uint'],'mscdecl',(...args)=>{calls.push(['actor50',...args]);return 1;});
 replace(0x2c858,'void',['int'],'mscdecl',arg=>{calls.push(['scene',arg]);});
 Interceptor.flush();
 const h48=new NativeFunction(b.add(0x13010),'uint',['pointer'],'mscdecl');
 const h50=new NativeFunction(b.add(0x132d4),'uint',['pointer'],'mscdecl');
 const obj=Memory.alloc(64);
 for(const flag of [0,1]){
  condition=flag;values=[18,33,34,3,17];reads=[];calls=[];
  const ret=h48(obj);rows.push({opcode:48,condition,ret,reads,calls});
 }
 for(const flag of [0,1])for(const mode of [0,1,2,65535])for(const sceneValue of [0,50]){
  condition=flag;scene=sceneValue;values=[mode,18,3,33,34,2];reads=[];calls=[];
  b.add(0xb2c50+3*36+12).writeU8(2);b.add(0x92f90+0x2044+3*64).writeU32(99);
  const ret=h50(obj);rows.push({opcode:50,condition,mode,scene,ret,reads,calls});
 }
 return rows;
}};'''
device=frida.get_local_device()
pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'))
session=None
try:
 session=device.attach(pid);script=session.create_script(source);script.load();rows=script.exports_sync.verify()
 for row in rows:
  if row['opcode']==48:
   expected=[['actor48',18]] if row['condition'] else [['effect48',18,33,34,0,3,17]]
   ret=1;tags=[2,4,4,43,13]
  else:
   tags=[64,2,4,4,4,43]
   if not row['condition']:
    expected=[['effect50',4114,33,34,2]]
    ret=1 if row['scene']==50 else 2
    if row['scene']==50:expected.append(['scene',0])
   elif row['mode'] in (0,65535):expected=[['actor50',18,33,34,2]];ret=1
   elif row['mode']==1:expected=[['actor50',99,33,34,2]];ret=1
   else:expected=[];ret=0
  row['match']=row['calls']==expected and row['ret']==ret and row['reads']==tags
 result={'scope':'Native handler control and argument forwarding; readers, condition, scene getter and effect leaves controlled','rows':rows,'passed':all(row['match'] for row in rows)}
 (ROOT/'analysis/native-eex-48-50-success-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(f"Native EEX 48/50 success branches: {sum(row['match'] for row in rows)}/{len(rows)}")
 if not result['passed']:
  print(next(row for row in rows if not row['match']));raise SystemExit(1)
finally:
 device.kill(pid)
 if session:session.detach()
