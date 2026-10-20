"""Validate original multi-target score aggregation with controlled effect eligibility."""
import itertools
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def expected(c):
    base=c['base']
    if not c['targets']:
        return max(0, 0 if base<5 else base-4)
    total=0
    for target in c['targets']:
        eligible=bool(c['eligible']&(1<<(target-1)))
        category=c['category']
        if category==0:
            if c['effect']==255:
                total+=10 if c['damage']>=c['hp'] else 4 if c['damage']*10//100 else 0
            elif eligible:
                total+=6 if target==1 else 3
        elif category==1 and eligible and c['hp']*100//100<60:
            total+=5
        elif category in (2,3,4) and eligible and c['state']<4:
            total+=3
        elif category==5 and eligible and c['flags']:
            total+=3
    return max(0,base+total)


def main():
    scenarios=[dict(damage=d,hp=h,state=s,flags=f,eligible=e)
               for d,h,s,f,e in ((9,100,3,0,3),(10,100,4,1,3),(100,100,3,1,3),
                                 (9,59,3,1,3),(9,60,4,0,3),(0,100,3,1,0),
                                 (10,100,3,1,1),(10,100,4,1,2),
                                 (9,59,4,1,1),(10,60,3,0,2),(40,40,3,1,3),(9,100,4,0,0))]
    cases=[]
    for targets,category,base,effect,scenario in itertools.product(
            ([],[1],[1,2],[1,1],[2,1,2]),range(7),(-5,0,4,5,80),(0,255),scenarios):
        cases.append(dict(targets=targets,category=category,base=base,effect=effect,**scenario))
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
 const b=Process.mainModule.base,keep=[],list=Memory.alloc(116);let current;
 function replace(offset,ret,args,abi,fn){const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);Interceptor.replace(b.add(offset),cb);}
 replace(0x3BC4B,'uint',['pointer','pointer','int','int'],'thiscall',()=>current.damage);
 replace(0x0721B,'uint',['pointer','uint'],'fastcall',()=>100);
 replace(0x390EF,'int',['uint8','uint8','uint8'],'mscdecl',(_a,target,_effect)=>(current.eligible&(1<<(target-1)))?1:0);
 Interceptor.flush();
 const score=new NativeFunction(b.add(0x38D96),'int',['pointer','int','uint8','uint8','uint8'],'mscdecl');
 b.add(0xB2C50+8).writeU8(1);const rows=[];
 for(const c of cases){
  current=c;list.writeByteArray(c.targets.concat([255]));
  for(const target of [1,2]){
   const slot=b.add(0xB2C50+target*36);slot.writeByteArray(new Uint8Array(36));slot.writeU32(target);
   slot.add(16).writeU32(c.hp);slot.add(24).writeU8(c.state);slot.add(25).writeU8(c.state);slot.add(30).writeU8(c.flags);
  }
  rows.push(score(list,c.base,c.category,0,c.effect));
 }
 return rows;
}};
''')
        script.load();rows=script.exports_sync.verify(cases)
        results=[dict(input=c,expected=expected(c),actual=r,match=expected(c)==r) for c,r in zip(cases,rows)]
        report=dict(function='0x438D96',passed=sum(r['match'] for r in results),total=len(results),rows=results,
                    scope='native multi-target iteration/category scoring, empty-list penalty, duplicate entries and zero floor; damage/maxHP100/effect eligibility supplied; target geometry and actual effect eligibility not verified')
        (ROOT/'analysis/native-ai-multi-target-score-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(f'Native AI multi-target score aggregation: {report["passed"]}/{len(results)}')
        if report['passed']!=len(results):
            print(next(r for r in results if not r['match']));raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
