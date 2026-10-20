"""Verify native party filtering, intercepting only the interactive chooser boundary."""
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def expected(case):
    required=[] if 0 in case['excluded'] else [0]
    required.extend(i for i in case['forced'] if i not in (0,65535) and i in case['available'])
    limit=max(case['limit'],len(required))
    candidates=required[:]
    dialog=len(required)!=limit
    if dialog:
        candidates.extend(i for i in sorted(case['available']) if i not in candidates and i not in case['excluded'])
    return dict(limit=limit,required=len(required),candidates=candidates,dialog=dialog,
                selected=candidates[:limit] if dialog else required)


def main():
    cases=[dict(name='Cao-only-automatic',available=[0,1,2,3],forced=[],excluded=[],limit=1),
           dict(name='choose-more',available=[0,1,2,3],forced=[],excluded=[],limit=3),
           dict(name='exclude-Cao',available=[0,1,2,3],forced=[],excluded=[0],limit=2),
           dict(name='forced-and-unavailable',available=[0,1,2,3],forced=[2,4],excluded=[],limit=3),
           dict(name='forced-overrides-excluded',available=[0,1,2,3],forced=[2],excluded=[2],limit=3),
           dict(name='raise-small-limit',available=[0,1,2,3],forced=[2,3],excluded=[],limit=1),
           dict(name='duplicate-forced',available=[0,1,2,3],forced=[2,2],excluded=[],limit=1),
           dict(name='implicit-Cao-availability',available=[1,2],forced=[],excluded=[],limit=1),
           dict(name='empty-after-exclusions',available=[0],forced=[],excluded=[0],limit=1)]
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
 const b=Process.mainModule.base,keep=[],selected=Memory.alloc(16*4);let chooser=null;
 function identity(p){return p.readU16()&4095;}
 const choose=new NativeCallback((list,required,limit)=>{
  const candidates=[];for(let i=0;i<32;i++){const p=list.add(i*4).readPointer();if(p.isNull())break;candidates.push(identity(p));}
  chooser={required,limit,candidates};
  selected.writeByteArray(new Uint8Array(16*4));
  for(let i=0;i<Math.min(limit,candidates.length);i++)selected.add(i*4).writePointer(b.add(0xA1B68+candidates[i]*72));
  return selected;
 },'pointer',['pointer','uint','int'],'mscdecl');
 keep.push(choose);Interceptor.replace(b.add(0x5E6B3),choose);Interceptor.flush();
 const select=new NativeFunction(b.add(0x1856A),'uint',[],'mscdecl');
 return cases.map(c=>{
  for(let i=0;i<512;i++){const u=b.add(0xA1B68+i*72);u.writeU16(i|4096);u.add(42).writeU8(c.available.includes(i)?0:255);}
  for(let i=0;i<5;i++){
   b.add(0xB09F0+i*4).writeU32(i<c.forced.length?c.forced[i]:65535);
   b.add(0xB0A04+i*4).writeU32(i<c.excluded.length?c.excluded[i]:65535);
  }
  b.add(0xB09EC).writeU8(c.limit);chooser=null;
  const status=select()&255,ids=[];
  for(let i=0;i<16;i++){const value=b.add(0x8B350+i*4).readU32();if(value===65535)break;ids.push(value);}
  return {status,limit:b.add(0xB09EC).readU8(),selected:ids,chooser};
 });
}};
''');script.load();actual=script.exports_sync.verify(cases)
        rows=[]
        for case,row in zip(cases,actual):
            wanted=expected(case)
            chooser=dict(required=wanted['required'],limit=wanted['limit'],candidates=wanted['candidates']) if wanted['dialog'] else None
            rows.append(dict(input=case,expected=wanted,actual=row,
                             match=row==dict(status=int(bool(wanted['selected'])),limit=wanted['limit'],selected=wanted['selected'],chooser=chooser)))
        report=dict(function='0x41856A',rows=rows,passed=sum(r['match'] for r in rows),total=len(rows),
                    scope='real forced/excluded/availability filtering and party writer;0x45E6B3 modal boundary replaced by deterministic first-N choice; no original UI interaction or campaign roster')
        (ROOT/'analysis/native-party-selection-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(f'Native party selection/filtering: {report["passed"]}/{len(rows)}')
        if report['passed']!=len(rows):
            print([r for r in rows if not r['match']]);raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
