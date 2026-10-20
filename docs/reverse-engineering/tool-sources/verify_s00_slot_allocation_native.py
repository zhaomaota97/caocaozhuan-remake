"""Run native slot constructors and scene-record allocator with external leaves controlled."""
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def main():
    capture=json.loads((ROOT/'analysis/native-s00-unit-setup-replay.json').read_text(encoding='utf-8'))
    snapshots=[r for r in capture['rows'] if r.get('state_after')]
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(snapshots){
 const b=Process.mainModule.base,keep=[],buffer=Memory.alloc(0x5000);let calls=[];
 function replace(rva,ret,args,abi,fn){const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);Interceptor.replace(b.add(rva),cb);}
 replace(0x0E090,'pointer',['pointer'],'fastcall',()=>buffer);
 replace(0x1B51E,'uint',['pointer','int','pointer'],'mscdecl',()=>1);
 replace(0x1B606,'void',['int','int','int'],'mscdecl',()=>{});
 replace(0x1A190,'uint',['int'],'mscdecl',()=>0);
 replace(0x4274C,'void',['pointer','int','uint','uint8','uint8'],'thiscall',(slot,id,flags,x,y)=>{
  calls.push({slot:slot.sub(b.add(0xB2C50)).toInt32()/36,id,flags,x,y,slot4:slot.add(4).readU8()});
 });
 replace(0x42890,'void',['pointer','int8','uint8'],'thiscall',()=>{});
 replace(0x429F9,'uint',['pointer','uint8','uint','uint8'],'thiscall',()=>0);
 replace(0x0721B,'uint',['pointer','uint'],'fastcall',()=>100);
 replace(0x0724A,'uint',['pointer','uint'],'fastcall',()=>50);
 replace(0x3F6CD,'void',['pointer','uint','uint'],'fastcall',()=>{});
 replace(0x3F70E,'void',['pointer','uint','uint'],'fastcall',()=>{});
 replace(0x59D8B,'uint',['int','uint8','int','uint8','uint8'],'mscdecl',()=>1);
 Interceptor.flush();
 const initialize=new NativeFunction(b.add(0x42613),'void',['pointer','uint8'],'thiscall');
 const allocate=new NativeFunction(b.add(0x4CC85),'void',[],'mscdecl');
 const constructors=[];
 for(let i=0;i<115;i++){
  const slot=b.add(0xB2C50+i*36);slot.writeByteArray(new Uint8Array(36).fill(165));initialize(slot,i);
  constructors.push({slot:i,slot4:slot.add(4).readU8(),id:slot.readU32(),type:slot.add(12).readU8(),coordinates:[slot.add(6).readU8(),slot.add(7).readU8()]});
 }
 const allocations=[];
 for(const s of snapshots){b.add(0x92F90).writeByteArray(s.state_after);calls=[];allocate();allocations.push({opcode:s.opcode,calls});}
 return {constructors,allocations};
}};
''')
        script.load();result=script.exports_sync.verify(snapshots)
        for r in result['constructors']:
            r['match']=(r['slot4']==r['slot'] and r['id']==65535 and r['type']==0 and r['coordinates']==[255,255])
        for source,row in zip(snapshots,result['allocations']):
            raw=bytes(source['state_after']);counters={0:0,2:15,1:35};expected=[]
            for i in range(115):
                record=raw[0x2044+i*64:0x2044+(i+1)*64]
                identity=int.from_bytes(record[:4],'little')
                if identity==65535:continue
                flags=int.from_bytes(record[8:12],'little');key=flags&3;key=key if key in (0,2) else 1
                slot=counters[key];counters[key]+=1
                expected.append(dict(slot=slot,id=identity,flags=flags,x=record[4],y=record[5],slot4=slot))
            row['expected']=expected;row['match']=row['calls']==expected
        result['scope']='native0x442613 constructors and0x44CC85 routing; expansion/stats/equipment/script/load leaves replaced; no full battlefield initialization'
        result['passed']=all(r['match'] for r in result['constructors']+result['allocations'])
        (ROOT/'analysis/native-s00-slot-allocation-validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print('Native constructors:',sum(r['match'] for r in result['constructors']),'/115; allocations:',[(r['opcode'],len(r['calls']),r['match']) for r in result['allocations']])
        if not result['passed']:raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
