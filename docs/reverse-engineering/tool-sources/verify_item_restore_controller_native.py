"""Execute native HP/MP consumable controllers with presentation leaves suppressed."""
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(){
 const b=Process.mainModule.base,keep=[];let maximum=100;
 function replace(rva,ret,args,abi,fn){const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);Interceptor.replace(b.add(rva),cb);}
 for(const rva of [0x721b,0x724a])replace(rva,'uint',['pointer','uint'],'fastcall',()=>maximum);
 replace(0x1c762,'void',['pointer','int'],'thiscall',()=>{});
 replace(0x55123,'void',['pointer','uint8','uint8','uint'],'thiscall',()=>{});
 replace(0x50984,'void',['uint','uint','int','int','uint','uint','uint','int'],'mscdecl',()=>{});
 replace(0x5533d,'uint8',['pointer','uint8','int8','int8','uint8'],'thiscall',()=>0);
 Interceptor.flush();
 const actor=b.add(0xb2c50),unit=b.add(0xa1b68),item=b.add(0xa1140),action=Memory.alloc(0x40);
 unit.writeByteArray(new Uint8Array(72));item.writeByteArray(new Uint8Array(25));
 const init=new NativeFunction(b.add(0x1dbbc),'void',['pointer','uint8','uint8'],'thiscall');
 const hp=new NativeFunction(b.add(0x1ccdf),'void',['pointer','int'],'thiscall');
 const mp=new NativeFunction(b.add(0x1ce3d),'void',['pointer'],'fastcall');
 const rows=[];
 for(const category of [63,64])for(const value of [0,1,30,254,255])for(const max of [100,250,500])for(const current of [0,1,99,max]){
  maximum=max;actor.writeByteArray(new Uint8Array(36));actor.writeU32(0);actor.add(16).writeU32(current);actor.add(20).writeU32(current);
  item.add(17).writeU8(category);item.add(21).writeU8(value);action.writeByteArray(new Uint8Array(0x40));init(action,0,0);
  if(category===63)hp(action,0);else mp(action);
  rows.push({category,value,maximum,current,hp:actor.add(16).readU32(),mp:actor.add(20).readU32()});
 }
 return rows;
}};
''');script.load();rows=script.exports_sync.capture()
    for row in rows:
        amount=row['maximum']-row['current'] if row['value']==255 else min(row['value'],row['maximum']-row['current'])
        hp=min(row['maximum'],row['current']+amount) if row['category']==63 else row['current']
        mp=min(row['maximum'],row['current']+(amount&255)) if row['category']==64 else row['current']
        row['match']=row['hp']==hp and row['mp']==mp
    result=dict(total=len(rows),passed=sum(row['match'] for row in rows),rows=rows,scope='native 0x41DBBC and HP/MP controllers, eligibility, amount, setters active; maxima and target-selector/presentation/camera leaves controlled; not inventory usage')
    text=json.dumps(result,indent=2)+'\n'
    (ROOT/'analysis/native-item-restore-controller.json').write_text(text,encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-item-restore-controller.json').write_text(text,encoding='utf-8')
    print(f'Native item restore controller: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(row for row in rows if not row['match']))
finally:
    device.kill(pid)
    if session:session.detach()
