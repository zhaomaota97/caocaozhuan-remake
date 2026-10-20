"""Differential-check original RNG outputs, state advancement, bounds, and chances."""
import json
from pathlib import Path
import frida
from game_rng import GameRng

ROOT=Path(__file__).resolve().parents[1]


def main():
    seeds=[0,1,0x7fffffff,0xffffffff]
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(seeds){
  const b=Process.mainModule.base,state=b.add(0x8ecd4);
  const draw=new NativeFunction(b.add(0x7fae7),'uint',[],'mscdecl');
  const bounded=new NativeFunction(b.add(0x7fb13),'uint',['uint'],'mscdecl');
  const chance=new NativeFunction(b.add(0x7fb32),'bool',['uint'],'mscdecl');
  const rows=[];
  for(const seed of seeds){
    state.writeU32(seed);const values=[];
    for(let i=0;i<1000;i++)values.push(draw());
    rows.push({seed,kind:'sequence',values,state:state.readU32()});
    for(const bound of [0,1,2,7,100,32768,65535]){
      state.writeU32(seed);const values=[];
      for(let i=0;i<25;i++)values.push(bounded(bound));
      rows.push({seed,kind:'bounded',bound,values,state:state.readU32()});
    }
    for(const percent of [0,1,50,99,100,101]){
      state.writeU32(seed);const values=[];
      for(let i=0;i<25;i++)values.push(chance(percent));
      rows.push({seed,kind:'chance',percent,values,state:state.readU32()});
    }
  }
  return rows;
}};
''')
        script.load();rows=script.exports_sync.verify(seeds)
        for row in rows:
            rng=GameRng(row['seed'])
            if row['kind']=='sequence':values=[rng.draw() for _ in row['values']]
            elif row['kind']=='bounded':values=[rng.bounded(row['bound']) for _ in row['values']]
            else:values=[rng.chance(row['percent']) for _ in row['values']]
            row['match']=values==row['values'] and rng.state==row['state']
        (ROOT/'analysis/native-rng-validation.json').write_text(
            json.dumps(rows,indent=2),encoding='utf-8')
        checks=sum(len(r['values']) for r in rows)
        print(f'Native RNG: {checks} draws in {sum(r["match"] for r in rows)}/{len(rows)} matching batches')
        if len(rows)!=56 or not all(r['match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
