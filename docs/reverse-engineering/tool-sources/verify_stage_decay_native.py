"""Validate native six-stage turn decay, probabilistic recovery, and RNG order."""
import itertools
import json
from pathlib import Path
import frida
from game_rng import GameRng

ROOT=Path(__file__).resolve().parents[1]


def main():
    cases=[dict(current=c,base=b,equipped=e,seed=s)
           for c,b,e,s in itertools.product([*range(8),255],(0,25,50,51,100),(False,True),range(8))]
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
  const b=Process.mainModule.base,actor=b.add(0xb2c50),unit=b.add(0xa1b68),keep=[];
  for(const [rva,args,abi] of [[0x3e69f,['uint8','uint8','uint8'],'mscdecl'],
      [0x3fcc9,['pointer'],'fastcall'],[0x79a01,['uint'],'mscdecl']]){
    const cb=new NativeCallback(()=>{},'void',args,abi);keep.push(cb);Interceptor.replace(b.add(rva),cb);
  }
  Interceptor.flush();
  const decay=new NativeFunction(b.add(0x3c975),'void',['pointer'],'fastcall');
  return cases.map(c=>{
    unit.writeByteArray(new Uint8Array(72));unit.add(0x25).writeU8(c.base);
    for(const off of [0x2e,0x31,0x34])unit.add(off).writeU8(255);
    if(c.equipped){unit.add(0x34).writeU8(0);b.add(0xa1140+17).writeU8(0x14);}
    actor.writeByteArray(new Uint8Array(36));actor.add(12).writeU8(2);
    actor.add(24).writeByteArray(new Uint8Array(6).fill(c.current));
    b.add(0x8ecd4).writeU32(c.seed);decay(actor);
    return {stages:Array.from(new Uint8Array(actor.add(24).readByteArray(6))),state:b.add(0x8ecd4).readU32()};
  });
}};
''')
        script.load();actual=script.exports_sync.verify(cases);rows=[]
        for case,native in zip(cases,actual):
            rng=GameRng(case['seed']);values=[]
            for _ in range(6):
                value=case['current']
                if value<2:value+=1
                elif value==2:
                    if rng.chance(100 if case['equipped'] else case['base']):value=3
                elif value==4:
                    if rng.chance(60-case['base'] if case['base']<51 else 10):value=3
                elif value>=5:value-=1
                values.append(value)
            rows.append(dict(**case,expected=values,actual=native['stages'],expected_seed=rng.state,
                actual_seed=native['state'],match=values==native['stages'] and rng.state==native['state']))
        (ROOT/'analysis/native-stage-decay-validation.json').write_text(
            json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Native stage decay: {sum(r["match"] for r in rows)}/{len(rows)}')
        if len(rows)!=720 or not all(r['match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
