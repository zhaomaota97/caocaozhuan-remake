"""Probe native stat-fruit writes, rank cap and actor attribute-state update."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(){
 const b=Process.mainModule.base,keep=[];function replace(rva,ret,args,abi,fn){const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);Interceptor.replace(b.add(rva),cb);}
 replace(0x1c762,'void',['pointer','int'],'thiscall',a=>a.add(28).writeU32(1));
 replace(0x5533d,'uint8',['pointer','uint8','int8','int8','uint8'],'thiscall',()=>0);Interceptor.flush();
 const actor=b.add(0xb2c50),unit=b.add(0xa1b68),item=b.add(0xa1140),action=Memory.alloc(64),rows=[];
 const init=new NativeFunction(b.add(0x1dbbc),'void',['pointer','uint8','uint8'],'thiscall');
 const apply=new NativeFunction(b.add(0x1d080),'void',['pointer'],'fastcall');
 for(const category of [70,71,72,73,74])for(const value of [0,1,2,5,255])for(const stat of [10,254,255])for(const rank of [24,49,50])for(const state of [0,2,3,4,6]){
  actor.writeByteArray(new Uint8Array(36));unit.writeByteArray(new Uint8Array(72));item.writeByteArray(new Uint8Array(25));action.writeByteArray(new Uint8Array(64));
  for(let i=0;i<5;i++){unit.add(21+i).writeU8(stat);unit.add(33+i).writeU8(rank);actor.add(24+i).writeU8(state);}
  item.add(17).writeU8(category);item.add(21).writeU8(value);init(action,0,0);apply(action);
  rows.push({category,value,stat,rank,state,stats:Array.from(new Uint8Array(unit.add(21).readByteArray(5))),ranks:Array.from(new Uint8Array(unit.add(33).readByteArray(5))),states:Array.from(new Uint8Array(actor.add(24).readByteArray(5)))});
 }
 return rows;
}};
''');script.load();rows=script.exports_sync.capture()
    for r in rows:
        index={70:0,71:2,72:1,73:3,74:4}[r['category']];gain=r['value']//2
        stats=[r['stat']]*5;ranks=[r['rank']]*5;states=[r['state']]*5
        stats[index]=min(255,r['stat']+gain);ranks[index]=min(50,r['rank']+gain);states[index]=3 if r['state']<3 else 6
        r['match']=r['stats']==stats and r['ranks']==ranks and r['states']==states
    result=dict(total=len(rows),passed=sum(r['match'] for r in rows),rows=rows,scope='native 0x41D080 with initializer/getters/setters/0x43F98E active; selection and item presentation controlled; no stock dispatch')
    text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/native-stat-fruit-controller.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-stat-fruit-controller.json').write_text(text,encoding='utf-8')
    print(f'Native stat-fruit controller: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(r for r in rows if not r['match']))
finally:
    device.kill(pid)
    if session:session.detach()
