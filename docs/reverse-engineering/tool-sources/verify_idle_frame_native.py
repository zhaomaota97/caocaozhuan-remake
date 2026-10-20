"""Validate native idle-frame selection across direction, flags, phase, and health."""
import itertools
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def expected(case):
    direction={0:1,1:2,2:0,3:2}[case['direction']]
    flagged=bool(case['flags']&6)
    frame=9 if case['health']<20 or case['flags']&32 else direction+6 if flagged else direction*2
    if not flagged:
        frame+=bool(case['phase']>>2) if case['status']&2 else bool(case['phase']&1)
    return frame


def main():
    cases=[dict(direction=d,flags=f,status=s,phase=p,health=h)
           for d,f,s,p,h in itertools.product(range(4),(0,2,4,6,32),(0,2),range(8),(19,20))]
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
  const b=Process.mainModule.base,unit=b.add(0xa1b68),actor=b.add(0xb2c50);
  unit.writeByteArray(new Uint8Array(72));unit.add(0x1c).writeU32(100);
  for(const off of [0x2e,0x31,0x34])unit.add(off).writeU8(255);
  const pixels=Memory.alloc(0x6300),v=b.add(0xaab80);
  v.add(4).writeU32(0x6300);v.add(12).writePointer(pixels);v.add(16).writeU8(1);
  const select=new NativeFunction(b.add(0x3e572),'pointer',['int'],'mscdecl');
  return cases.map(c=>{
    actor.writeByteArray(new Uint8Array(36));
    actor.add(15).writeU8(c.direction);actor.add(13).writeU8(c.flags);
    actor.add(30).writeU8(c.status);actor.add(16).writeU32(c.health);
    b.add(0xb3d08+5).writeU8(c.phase);
    return select(0).sub(pixels).toInt32()/2304;
  });
}};
''')
        script.load();actual=script.exports_sync.verify(cases)
        rows=[dict(**c,expected=expected(c),actual=a,match=expected(c)==a) for c,a in zip(cases,actual)]
        (ROOT/'analysis/native-idle-frame-validation.json').write_text(
            json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Native idle frames: {sum(r["match"] for r in rows)}/{len(rows)}')
        if len(rows)!=640 or not all(r['match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
