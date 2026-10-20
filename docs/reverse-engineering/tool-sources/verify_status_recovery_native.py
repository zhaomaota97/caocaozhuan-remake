"""Validate native status recovery in an isolated cell without support neighbors."""
import itertools
import json
from pathlib import Path
import frida
from game_rng import GameRng

ROOT=Path(__file__).resolve().parents[1]


def main():
    cases=[dict(status=c,base=b,equipped=e,seed=s)
           for c,b,e,s in itertools.product([*range(32),255],(0,15,25,50,100),(False,True),range(8))]
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
  b.add(0xb422c).writeU8(1);b.add(0xb422d).writeU8(1);
  b.add(0xb2c48).writeU32(1);
  const recover=new NativeFunction(b.add(0x3c7d6),'void',['pointer'],'fastcall');
  return cases.map(c=>{
    unit.writeByteArray(new Uint8Array(72));unit.add(0x25).writeU8(c.base);
    for(const off of [0x2e,0x31,0x34])unit.add(off).writeU8(255);
    if(c.equipped){unit.add(0x34).writeU8(0);b.add(0xa1140+17).writeU8(0x14);}
    actor.writeByteArray(new Uint8Array(36));actor.add(12).writeU8(2);actor.add(30).writeU8(c.status);
    b.add(0x8ecd4).writeU32(c.seed);recover(actor);
    return {status:actor.add(30).readU8(),state:b.add(0x8ecd4).readU32()};
  });
}};
''')
        script.load();actual=script.exports_sync.verify(cases);rows=[]
        for case,native in zip(cases,actual):
            rng=GameRng(case['seed']);value=case['status'];probability=100 if case['equipped'] else case['base']
            for bit in (2,4,8,16):
                if value&bit:
                    clears=(True if probability==100 else rng.chance(max(probability-15,10))) if bit==8 else rng.chance(probability)
                    if clears:value&=~(bit|0x80)
            rows.append(dict(**case,expected=value,actual=native['status'],expected_seed=rng.state,
                actual_seed=native['state'],match=value==native['status'] and rng.state==native['state']))
        (ROOT/'analysis/native-status-recovery-validation.json').write_text(
            json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Native status recovery: {sum(r["match"] for r in rows)}/{len(rows)}')
        if len(rows)!=2640 or not all(r['match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
