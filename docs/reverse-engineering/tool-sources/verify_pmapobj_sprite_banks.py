"""Map all PMAPOBJ pairs to four direction banks and verify native mirror/addressing."""
import hashlib
import json
from pathlib import Path
import frida
from export_map_layouts import entries
ROOT=Path(__file__).resolve().parents[1]
resources=dict(entries(ROOT/'Pmapobj.e5'))
assert len(resources)==412 and all(len(raw)==0xf000 for raw in resources.values())
def mirror(raw):
 return b''.join(raw[i:i+48][::-1] for i in range(0,len(raw),48))
records=[]
for object_id in range(206):
 even,odd=resources[object_id*2],resources[object_id*2+1]
 banks=[odd,mirror(even),even,mirror(odd)]
 records.append({'objectId':object_id,'resourceIndices':[object_id*2,object_id*2+1],
                 'bankBytes':0x3c000,'frameWidth':48,'frameHeight':64,'framesPerDirection':20,
                 'directions':[{'direction':d,'sourceResource':object_id*2+(d in (0,3)),
                                'mirrorX':d in (1,3),'sha256':hashlib.sha256(raw).hexdigest()} for d,raw in enumerate(banks)]})
sample_ids=[0,1,410,411]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(samples){
 const b=Process.mainModule.base,mirror=new NativeFunction(b.add(0x1ee53),'void',['uint16','int','pointer','pointer'],'mscdecl');
 const address=new NativeFunction(b.add(0x2b010),'pointer',['pointer'],'fastcall'),obj=Memory.alloc(64),bank=Memory.alloc(0x3c000),mirrors=[],addresses=[];
 for(const sample of samples){const src=Memory.alloc(sample.length),dst=Memory.alloc(sample.length);src.writeByteArray(sample);mirror(48,1280,src,dst);mirrors.push(Array.from(new Uint8Array(dst.readByteArray(sample.length))));}
 obj.writeByteArray(new Uint8Array(64));obj.add(16).writePointer(bank);
 for(let direction=0;direction<4;direction++)for(let frame=0;frame<20;frame++){
  obj.add(0x2e).writeU16(direction);obj.add(0x2a).writeU16(frame);addresses.push({direction,frame,offset:address(obj).sub(bank).toInt32()});
 }
 return {mirrors,addresses};
}};''');script.load();result=script.exports_sync.verify([list(resources[i]) for i in sample_ids])
 mirror_checks=[{'resourceIndex':i,'bytes':len(resources[i]),'match':bytes(value)==mirror(resources[i])} for i,value in zip(sample_ids,result.pop('mirrors'))]
 for row in result['addresses']:row['match']=row['offset']==(row['direction']*20+row['frame'])*3072
 out={'scope':'All 412 real resource sizes and 206 pair mappings; 4 native full-sheet mirrors and 80 native frame addresses; loader branch mapping static','objects':records,'nativeMirrors':mirror_checks,'nativeAddresses':result['addresses'],
      'passed':len(mirror_checks)==4 and len(result['addresses'])==80 and all(r['match'] for r in mirror_checks+result['addresses'])}
 (ROOT/'analysis/pmapobj-sprite-bank-mapping.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print(f"PMAPOBJ: 412 resources / 206 objects; native mirrors {sum(r['match'] for r in mirror_checks)}/4; frame addresses {sum(r['match'] for r in result['addresses'])}/80")
 if not out['passed']:raise SystemExit(1)
finally:
 device.kill(pid)
 if session:session.detach()
