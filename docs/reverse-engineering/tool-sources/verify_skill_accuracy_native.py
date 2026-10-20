"""Validate elemental accuracy with real qualification, equipment, and state branches."""
import itertools
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def expected(c):
    if c['terrain']==255:return 0
    if c['status']&8:return 100
    a,d=c['attack']*2,c['defend']*2
    if a>=2*d:chance=100
    elif a>=d:chance=90+(a-d)*10//d
    elif a>=d//2:chance=60+max(a-d//2,0)*30//(d//2)
    else:chance=30+max(a-d//3,0)*30//(d//3)
    chance=max(min(chance+c['bonus'],100)-c['reduction'],0)
    n,denom={0:(1,1),1:(9,10),3:(4,5),4:(3,5)}[c['effect']]
    return min(chance*n//denom,100)


def main():
    scenarios=[(0,0),(10,100),(33,100),(49,100),(50,100),(99,100),(100,100),(200,100)]
    cases=[dict(attack=a,defend=d,effect=e,status=s,terrain=t,bonus=b,reduction=r,reduction_code=k)
           for (a,d),e,s,t,(b,r,k) in itertools.product(scenarios,(0,1,3,4),(0,8),(0,255),
               ((0,0,0),(10,0,0),(0,15,0x36),(0,15,0x37)))]
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
  const b=Process.mainModule.base,unitA=b.add(0xa1b68),unitD=unitA.add(72);
  const actor=b.add(0xb2c50),target=actor.add(36),items=b.add(0xa1140);
  const map=Memory.alloc(0x641);map.writeByteArray(new Uint8Array(0x641));
  const v=b.add(0xaeb38);v.add(4).writeU32(0x641);v.add(12).writePointer(map);v.add(16).writeU8(1);
  b.add(0xb422c).writeU8(1);b.add(0xb422d).writeU8(1);
  const chance=new NativeFunction(b.add(0x3b73f),'uint',
    ['pointer','int','int','uint8'],'thiscall');
  return cases.map(c=>{
    for(const u of [unitA,unitD]){
      u.writeByteArray(new Uint8Array(72));
      for(const off of [0x2e,0x31,0x34])u.add(off).writeU8(255);
    }
    for(const off of [0x17,0x19]){
      unitA.add(off).writeU8(c.attack);unitD.add(off).writeU8(c.defend);
    }
    actor.writeByteArray(new Uint8Array(36));target.writeByteArray(new Uint8Array(36));
    target.writeU32(1);target.add(4).writeU8(1);target.add(30).writeU8(c.status);
    for(const a of [actor,target]){a.add(26).writeU8(3);a.add(28).writeU8(3);}
    items.writeByteArray(new Uint8Array(50));
    if(c.bonus){unitA.add(0x34).writeU8(0);items.add(17).writeU8(0x34);items.add(21).writeU8(c.bonus);}
    if(c.reduction){unitD.add(0x34).writeU8(1);items.add(25+17).writeU8(c.reduction_code);items.add(25+21).writeU8(c.reduction);}
    map.add(0x640).writeU8(c.terrain);
    return chance(actor,0,target.toInt32(),c.effect);
  });
}};
''')
        script.load();actual=script.exports_sync.verify(cases)
        rows=[dict(**c,expected=expected(c),actual=a,match=expected(c)==a) for c,a in zip(cases,actual)]
        (ROOT/'analysis/native-skill-accuracy-validation.json').write_text(
            json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Native skill accuracy: {sum(r["match"] for r in rows)}/{len(rows)}')
        if len(rows)!=512 or not all(r['match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
