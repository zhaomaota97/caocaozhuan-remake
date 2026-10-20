"""Validate actual native horizontal frame reversal and flag preservation."""
import json
from pathlib import Path
import frida

ROOT = Path(__file__).resolve().parents[1]
device = frida.get_local_device()
pid = device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'))
session = None
try:
    session = device.attach(pid)
    script = session.create_script('''
rpc.exports={verify(){
 const b=Process.mainModule.base;
 const frameBytes=115*0x6300,frames=Memory.alloc(frameBytes),scratch=Memory.alloc(0x1200);
 function view(rva,pixels,size){
  const v=b.add(rva);v.add(4).writeU32(size);v.add(12).writePointer(pixels);v.add(16).writeU8(1);
 }
 view(0xaab80,frames,frameBytes);view(0xaf490,scratch,0x1200);
 const actor=Memory.alloc(36);
 const mirror=new NativeFunction(b.add(0x3fd34),'void',['pointer','int'],'thiscall');
 const rows=[];
 function equal(actual,expected){
  for(let i=0;i<expected.length;i++)if(actual[i]!==expected[i])return false;
  return true;
 }
 for(const slot of [0,1,114])for(let flags=0;flags<256;flags++)for(const desired of [0,1]){
  const original=new Uint8Array(0x6300);
  for(let i=0;i<original.length;i++)original[i]=(i%48+3*Math.floor(i/48)+slot)&255;
  const input=frames.add(slot*0x6300);input.writeByteArray(original);
  actor.writeByteArray(new Uint8Array(36));actor.add(4).writeU8(slot);actor.add(13).writeU8(flags);
  const expected=new Uint8Array(original);
  const changed=((flags&8)!==0)!==(desired!==0);
  if(changed)for(const [offset,height] of [[0x2400,96],[0x4800,48]]){
   for(let y=0;y<height;y++)for(let x=0;x<48;x++)expected[offset+y*48+x]=original[offset+y*48+47-x];
  }
  mirror(actor,desired);
  const flagsExpected=desired ? flags|8 : flags&~8;
  const firstPixels=equal(new Uint8Array(input.readByteArray(0x6300)),expected);
  const firstFlags=actor.add(13).readU8()===flagsExpected;
  mirror(actor,desired);
  const repeatedPixels=equal(new Uint8Array(input.readByteArray(0x6300)),expected);
  const repeatedFlags=actor.add(13).readU8()===flagsExpected;
  mirror(actor,(flags&8)!==0 ? 1 : 0);
  const roundtripPixels=equal(new Uint8Array(input.readByteArray(0x6300)),original);
  const roundtripFlags=actor.add(13).readU8()===flags;
  rows.push({slot,flags,desired,changed,firstPixels,firstFlags,repeatedPixels,repeatedFlags,
   roundtripPixels,roundtripFlags});
 }
 return rows;
}};
''')
    script.load()
    rows = script.exports_sync.verify()
    checks = ('firstPixels','firstFlags','repeatedPixels','repeatedFlags','roundtripPixels','roundtripFlags')
    for row in rows:
        row['match'] = all(row[key] for key in checks)
    result = {'function':'0x43FD34','replacedFunctions':[],
              'total':len(rows),'matched':sum(row['match'] for row in rows),'rows':rows}
    (ROOT/'analysis/native-movement-mirroring.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f"Native movement pixel mirroring: {result['matched']}/{result['total']}")
    if len(rows)!=1536 or result['matched']!=len(rows):
        raise SystemExit('Native mirror mismatch; inspect output')
finally:
    device.kill(pid)
    if session:
        session.detach()
