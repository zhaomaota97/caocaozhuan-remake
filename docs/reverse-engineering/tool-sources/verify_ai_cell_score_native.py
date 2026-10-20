"""Differential probe of AI cell-score orchestration with controlled score leaves."""
import itertools
import json
from pathlib import Path
import frida

ROOT = Path(__file__).resolve().parents[1]


def expected(c):
    score, a, e = c['base'], 0, 0
    if c['occupied'] != 255 and not c['same']:
        return dict(score=score, maximum=c['maximum'], target=99, kind=88, position=[30,31])
    if not c['disabled']:
        if c['mode'] != 4:
            a = c['attack']
            if not c['effect_blocked']:
                e = c['effect']
            score = (score + max(a, e)) & 255
        score = min(255, score + c['terrain'])
        if c['same'] and a == 0:
            score = min(255, score + 1)
    if c['excluded']:
        score = 0
    if score > c['maximum']:
        return dict(score=score, maximum=score, target=41 if e > a else 31,
                    kind=17 if e > a else 255, position=[4,5])
    return dict(score=score, maximum=c['maximum'], target=99, kind=88, position=[30,31])


def main():
    cases=[]
    for base,attack,effect,terrain in itertools.product((0,250,255),(0,10,80),(0,10,90),(0,8,100)):
        for variation in ({},dict(same=True),dict(maximum=22),dict(maximum=255),
                          dict(disabled=True),dict(mode=4),dict(effect_blocked=True),
                          dict(occupied=5),dict(occupied=5,same=True),dict(excluded=True)):
            c=dict(base=base,attack=attack,effect=effect,terrain=terrain,same=False,
                   maximum=0,disabled=False,mode=0,effect_blocked=False,occupied=255,excluded=False)
            c.update(variation);cases.append(c)
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
 const b=Process.mainModule.base,grid=Memory.alloc(0x1400),actor=Memory.alloc(0x24),xy=Memory.alloc(2);
 const keep=[];let current;
 function replace(offset,ret,args,abi,fn){const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);Interceptor.replace(b.add(offset),cb);}
 replace(0x7FA40,'pointer',['pointer','uint','uint','uint'],'thiscall',()=>grid);
 replace(0x35884,'uint',['pointer'],'mscdecl',()=>current.occupied);
 replace(0x38965,'uint',['pointer','pointer','pointer'],'fastcall',()=>current.attack);
 replace(0x391DC,'uint',['pointer','pointer'],'thiscall',()=>current.effect);
 replace(0x3A4BF,'int',['pointer','pointer'],'thiscall',()=>current.terrain);
 Interceptor.flush();
 const calculate=new NativeFunction(b.add(0x3A529),'void',['pointer','pointer'],'thiscall');
 const rows=[];xy.writeByteArray([4,5]);b.add(0xB422C).writeU8(20);
 for(const c of cases){
  current=c;grid.writeByteArray(new Uint8Array(0x1400).fill(0));
  grid.add(104).writeU8(0);grid.add(0x640+104).writeU8(c.base);
  actor.writeByteArray(new Uint8Array(0x24));actor.add(6).writeByteArray(c.same?[4,5]:[10,10]);
  actor.add(13).writeU8(c.disabled?128:0);actor.add(14).writeU8(c.mode);actor.add(30).writeU8(c.effect_blocked?4:0);
  b.add(0xB2C30).writeU8(31);b.add(0xB2C2C).writeU8(41);b.add(0xB2C40).writeU8(17);
  b.add(0xB2C38).writeByteArray(c.excluded?[4,5]:[255,255]);b.add(0xB2C4C).writeU8(c.maximum);
  b.add(0xB2C28).writeU8(99);b.add(0xB2C44).writeU8(88);b.add(0xB2C20).writeByteArray([30,31]);
  calculate(actor,xy);
  rows.push({score:grid.add(0x640+104).readU8(),maximum:b.add(0xB2C4C).readU8(),
   target:b.add(0xB2C28).readU8(),kind:b.add(0xB2C44).readU8(),position:[b.add(0xB2C20).readU8(),b.add(0xB2C21).readU8()]});
 }
 return rows;
}};
''')
        script.load();rows=script.exports_sync.verify(cases)
        result=[]
        for c,row in zip(cases,rows):
            exp=expected(c);result.append(dict(input=c,expected=exp,actual=row,match=exp==row))
        report=dict(function='0x43A529',passed=sum(r['match'] for r in result),total=len(result),rows=result,
                    scope='native cell-score orchestration; resource buffer,occupancy,attack/effect/terrain score leaves replaced; not complete native AI decisions')
        (ROOT/'analysis/native-ai-cell-score-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(f'Native AI cell-score orchestration: {report["passed"]}/{len(result)}')
        if report['passed']!=len(result):
            print(next(r for r in result if not r['match']));raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
