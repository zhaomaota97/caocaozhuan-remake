"""Run original idle waiting controller with deterministic time/input/render leaves."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(){
 const b=Process.mainModule.base,keep=[];let tick=1000,stop=1025,frames=[];
 function replace(rva,ret,args,abi,fn){const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);Interceptor.replace(b.add(rva),cb);}
 replace(0x7eb97,'uint',[],'mscdecl',()=>tick);
 replace(0x2c56b,'int',[],'mscdecl',()=>{tick++;return tick>=stop?1:0;});
 replace(0x2b81b,'void',['uint'],'mscdecl',()=>{});
 replace(0x53e81,'void',['pointer','int'],'thiscall',()=>{});
 replace(0x53ea8,'void',['int'],'fastcall',()=>{});
 replace(0x53b13,'void',['pointer'],'fastcall',()=>frames.push({tick,phase:b.add(0xb3d08+5).readU8()}));Interceptor.flush();
 const run=new NativeFunction(b.add(0x55cb2),'void',['pointer'],'fastcall'),object=Memory.alloc(0x2000),rows=[];
 for(const phase of [0,7,255])for(const elapsed of [1,8,9,17,25]){
  tick=1000;stop=1000+elapsed;frames=[];b.add(0xb3d08+5).writeU8(phase);run(object);
  rows.push({phase,elapsed,frames,finalPhase:b.add(0xb3d08+5).readU8(),deadline:b.add(0xb1b18).readU32()});
 }
 return rows;
}};
''');script.load();rows=script.exports_sync.capture()
    for r in rows:
        phase=r['phase'];frames=[]
        for tick in range(1008,1000+r['elapsed'],8):phase=(phase+1)&7;frames.append(dict(tick=tick,phase=phase))
        r['match']=r['frames']==frames and r['finalPhase']==phase and r['deadline']==1008+len(frames)*8
    result=dict(total=len(rows),passed=sum(r['match'] for r in rows),rows=rows,scope='original 0x455CB2 idle loop and timer/phase helpers; deterministic clock/input, rendering callbacks suppressed; no full gameplay timing capture')
    text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/native-idle-phase-wait.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-idle-phase-wait.json').write_text(text,encoding='utf-8')
    print(f'Native idle phase wait controller: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(r for r in rows if not r['match']))
finally:
    device.kill(pid)
    if session:session.detach()
