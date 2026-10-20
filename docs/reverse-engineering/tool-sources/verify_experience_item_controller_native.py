"""Trace original XP-item controller ordering with controlled growth/presentation leaves."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(){
 const b=Process.mainModule.base,keep=[];let target=0,trace=[],grown=false;
 function replace(rva,ret,args,abi,fn){const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);Interceptor.replace(b.add(rva),cb);}
 replace(0x5533d,'uint8',['pointer','uint8','int8','int8','uint8'],'thiscall',()=>target);
 replace(0x1c762,'void',['pointer','int'],'thiscall',()=>{trace.push({kind:'presentation'});});
 replace(0x8950,'void',['pointer','uint','int'],'thiscall',(_unit,total,display)=>{trace.push({kind:'growth',total,display});grown=true;});
 replace(0x721b,'uint',['pointer','uint'],'fastcall',()=>grown?120:100);
 replace(0x724a,'uint',['pointer','uint'],'fastcall',()=>grown?60:50);
 replace(0x2f699,'void',['int'],'mscdecl',()=>{});Interceptor.flush();
 const actor=b.add(0xb2c50),unit=b.add(0xa1b68),item=b.add(0xa1140),action=Memory.alloc(64),rows=[];
 const init=new NativeFunction(b.add(0x1dbbc),'void',['pointer','uint8','uint8'],'thiscall');
 const apply=new NativeFunction(b.add(0x1d3d9),'void',['pointer'],'fastcall');
 for(const selected of [0,255])for(const level of [1,49,50])for(const xp of [0,99,255])for(const value of [0,1,100,255]){
  target=selected;trace=[];grown=false;
  actor.writeByteArray(new Uint8Array(36));unit.writeByteArray(new Uint8Array(72));item.writeByteArray(new Uint8Array(25));action.writeByteArray(new Uint8Array(64));
  actor.add(16).writeU32(10);actor.add(20).writeU32(5);unit.add(44).writeU8(level);unit.add(45).writeU8(xp);item.add(17).writeU8(75);item.add(21).writeU8(value);
  init(action,0,0);apply(action);
  rows.push({selected,level,xp,value,trace,hp:actor.add(16).readU32(),mp:actor.add(20).readU32()});
 }
 return rows;
}};
''');script.load();rows=script.exports_sync.capture()
    for r in rows:
        eligible=r['selected']!=255 and r['level']<50
        trace=[dict(kind='presentation'),dict(kind='growth',total=r['xp']+r['value'],display=1)] if eligible else []
        r['match']=r['trace']==trace and r['hp']==(120 if eligible else 10) and r['mp']==(60 if eligible else 5)
    result=dict(total=len(rows),passed=sum(r['match'] for r in rows),rows=rows,scope='original XP-item initializer/controller/eligibility and resource setters; target/presentation/growth/maxima leaves controlled; growth callback changes mocked maxima to prove ordering')
    text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/native-experience-item-controller.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-experience-item-controller.json').write_text(text,encoding='utf-8')
    print(f'Native experience item controller: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(r for r in rows if not r['match']))
finally:
    device.kill(pid)
    if session:session.detach()
