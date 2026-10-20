"""Run native range/filter/selection chain; only target scores and buffers supplied."""
import itertools
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def main():
    cases=[dict(side_mask=side,hp_mask=hp,scores=list(scores),shape=shape,xy=list(xy))
           for side,hp,scores,shape,xy in itertools.product(range(16),range(16),
               ((0,0,0,0),(10,10,10,10),(10,20,20,1),(256,511,512,1023)),(0,1),((4,5),(0,0),(7,7)))]
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
 const b=Process.mainModule.base,map=Memory.alloc(0x2800),battle=Memory.alloc(0x2800),actor=Memory.alloc(36),xy=Memory.alloc(2),keep=[];
 let current,visits=[];
 function replace(offset,ret,args,abi,fn){const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);Interceptor.replace(b.add(offset),cb);}
 replace(0x7FA40,'pointer',['pointer','uint','uint','uint'],'thiscall',(obj,offset)=>obj.equals(b.add(0xAEB38))?map.add(offset):battle.add(offset));
 replace(0x3F8BE,'uint',['pointer','uint'],'fastcall',()=>current.shape);
 replace(0x38A20,'uint',['pointer','uint8','uint'],'thiscall',(_actor,target,position)=>{visits.push({target,position:position&65535});return current.scores[target-1];});
 Interceptor.flush();
 const choose=new NativeFunction(b.add(0x38965),'uint',['pointer','pointer','pointer'],'fastcall');
 const cardinal=[],diagonal=[];
 for(let i=0;i<4;i++){
  cardinal.push([b.add(0x8DF68+i*8).readS32(),b.add(0x8DF6C+i*8).readS32()]);
  diagonal.push([b.add(0x8DF48+i*8).readS32(),b.add(0x8DF4C+i*8).readS32()]);
 }
 b.add(0xB2C48).writeU32(1);b.add(0xB422C).writeU8(8);b.add(0xB422D).writeU8(8);
 const rows=[];
 for(const c of cases){
  current=c;visits=[];map.writeByteArray(new Uint8Array(0x2800).fill(255));battle.writeByteArray(new Uint8Array(0x2800));
  actor.writeByteArray(new Uint8Array(36));xy.writeByteArray(c.xy);b.add(0xB2C50+4).writeU8(0);
  for(let i=0;i<4;i++){
   const slot=b.add(0xB2C50+(i+1)*36);slot.writeByteArray(new Uint8Array(36));
   slot.add(4).writeU8((c.side_mask&(1<<i))?35:0);slot.add(16).writeU32((c.hp_mask&(1<<i))?1:0);
   const x=c.xy[0]+cardinal[i][0],y=c.xy[1]+cardinal[i][1];
   if(x>=0&&x<8&&y>=0&&y<8)map.add(0xC80+x+y*8).writeU8(i+1);
  }
  b.add(0xB2C28).writeU8(255);b.add(0xB2C30).writeU8(77);
  const score=choose(actor,xy,xy)&255,candidates=[];
  for(let i=0;i<116;i++){const target=b.add(0xAC748+i).readU8();if(target===255)break;candidates.push(target);}
  rows.push({score,target:b.add(0xB2C30).readU8(),candidates,visits});
 }
 return {cardinal,diagonal,rows};
}};
''')
        script.load();native=script.exports_sync.verify(cases);results=[]
        for c,actual in zip(cases,native['rows']):
            candidates=[]
            for i,(dx,dy) in enumerate(native['cardinal']):
                x,y=c['xy'][0]+dx,c['xy'][1]+dy
                if 0<=x<8 and 0<=y<8 and c['side_mask']&(1<<i) and c['hp_mask']&(1<<i):
                    candidates.append(i+1)
            target=255;score=0
            for slot in candidates:
                value=c['scores'][slot-1]&255
                if value>score:score,target=value,slot
            exp=dict(score=score,target=target,candidates=candidates,
                     visits=[dict(target=s,position=c['xy'][0]+c['xy'][1]*256) for s in candidates])
            results.append(dict(input=c,expected=exp,actual=actual,match=exp==actual))
        report=dict(passed=sum(r['match'] for r in results),total=len(results),
                    cardinal=native['cardinal'],diagonal=native['diagonal'],rows=results,
                    scope='native0x438965->0x436586->geometry/filter/HP/faction/list; shapes0/1; damage score leaf and resource buffers supplied; no full AI turn')
        (ROOT/'analysis/native-ai-candidate-selection-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(f'Native AI candidate geometry/filter/selection: {report["passed"]}/{len(results)}; cardinal={native["cardinal"]}')
        if report['passed']!=len(results):
            print(next(r for r in results if not r['match']));raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
