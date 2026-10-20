"""Probe non-splash attack-score rules with controlled damage/range inputs."""
import itertools
import json
from pathlib import Path
import frida

ROOT = Path(__file__).resolve().parents[1]


def expected(c):
    score = 0
    if not c['same_side']:
        if c['damage'] >= c['hp']:
            score = 80
        elif c['damage'] * 10 // 100 or c['hp'] * 100 // 100 < 41:
            score = 16
        else:
            score = 10 if c['mode'] == 1 else 2
    if c['flag']:
        score += 8
    if score and c['identity'] < 174:
        score += 8 if c['identity'] == 10 or c['slot'] == 35 else 4
    if score < 75 and c['filtered']:
        return 0
    if c['risk'] and score > 1:
        score -= 1
    return score


def main():
    cases = [dict(zip(('hp','damage','mode','flag','identity','slot','risk','filtered','same_side'), values))
             for values in itertools.product((40,41,100),(0,9,10,40,100),(0,1),(0,8),
                                             (10,11,174),(0,35),(0,1),(0,1),(False,True))]
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
 const b=Process.mainModule.base,actor=Memory.alloc(0x24),grid=Memory.alloc(0x640),keep=[];let current;
 function replace(offset,ret,args,abi,fn){const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);Interceptor.replace(b.add(offset),cb);}
 replace(0x3BC4B,'uint',['pointer','pointer','int','int'],'thiscall',()=>current.damage);
 replace(0x0721B,'uint',['pointer','uint'],'fastcall',()=>100);
 replace(0x3FFED,'uint',['pointer'],'fastcall',()=>current.filtered);
 replace(0x07818,'uint',['pointer'],'fastcall',()=>0);
 replace(0x3F8BE,'uint',['pointer','uint'],'fastcall',()=>0);
 replace(0x7FA40,'pointer',['pointer','uint','uint','uint'],'thiscall',()=>grid);
 replace(0x36586,'uint',['pointer','pointer','uint','uint8','int8'],'thiscall',()=>{grid.add(104).writeU8(current.risk);return 0;});
 Interceptor.flush();
 const score=new NativeFunction(b.add(0x38A20),'uint',['pointer','uint8','uint'],'thiscall');
 b.add(0x92F90+0x3D06).writeU16(10);b.add(0xB422C).writeU8(20);
 const rows=[];
 for(const c of cases){
  current=c;actor.writeByteArray(new Uint8Array(0x24));actor.writeU32(0);actor.add(14).writeU8(c.mode);
  const target=b.add(0xB2C50+c.slot*0x24);target.writeByteArray(new Uint8Array(0x24));
  target.writeU32(c.identity);target.add(4).writeU8(c.same_side?0:35);
  target.add(6).writeByteArray([6,7]);target.add(16).writeU32(c.hp);target.add(30).writeU8(c.flag);
  rows.push(score(actor,c.slot,4+(5<<8)));
 }
 return rows;
}};
''')
        script.load();rows=script.exports_sync.verify(cases)
        result=[dict(input=c,expected=expected(c),actual=r,match=expected(c)==r) for c,r in zip(cases,rows)]
        report=dict(function='0x438A20',passed=sum(r['match'] for r in result),total=len(result),rows=result,
                    scope='non-splash attack scoring; damage,maxHP100,class-filter,range generation and resource buffer controlled; real faction/flags/HP/identity access and native score arithmetic; not full AI')
        (ROOT/'analysis/native-ai-attack-score-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(f'Native non-splash AI attack score: {report["passed"]}/{len(result)}')
        if report['passed']!=len(result):
            print(next(r for r in result if not r['match']));raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
