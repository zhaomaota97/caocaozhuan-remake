"""Draw a real PMAPOBJ frame through the original clipped blitter and compare all bytes."""
import hashlib
import json
from pathlib import Path
import frida
from export_map_layouts import entries
ROOT=Path(__file__).resolve().parents[1]
frame=next(raw for i,raw in entries(ROOT/'Pmapobj.e5') if i==1)[:3072]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(bytes){
 const b=Process.mainModule.base,source=Memory.alloc(bytes.length),dest=Memory.alloc(104*96+128),rows=[];source.writeByteArray(bytes);
 b.add(0xbd044).writeU32(0);b.add(0xb8598).writeU32(0);b.add(0xb859c).writeU32(0);b.add(0xb8a48).writeS32(-1);
 b.add(0xb9220).writeU32(104);b.add(0xba570).writeU32(104);b.add(0xba21c).writePointer(dest.add(64));b.add(0xb88b8).writeU32(7);b.add(0xbc018).writeU32(1);
 for(const [i,v] of [0,0,95,95].entries())b.add(0xbd120+i*4).writeS32(v);
 const draw=new NativeFunction(b.add(0x7e09b),'void',['int','int','uint','int','pointer'],'mscdecl');
 for(const mode of [0,1,2,3])for(const x of [-12,20,80])for(const y of [-20,10,80]){
  dest.writeByteArray(new Uint8Array(104*96+128).fill(0xa5));b.add(0xba3e0).writeU32(mode);b.add(0xb7a90).writeU32(0);b.add(0xb7c20).writeU32(0);
  draw(x,y,48,64,source);rows.push({mode,x,y,bytes:Array.from(new Uint8Array(dest.readByteArray(104*96+128)))});
 }
 return rows;
}};''');script.load();rows=script.exports_sync.verify(list(frame))
 for row in rows:
  expected=bytearray([0xa5])*(104*96+128)
  for sy in range(64):
   for sx in range(48):
    x,y=row['x']+sx,row['y']+sy
    if 0<=x<96 and 0<=y<96:
     i=64+y*104+x;src=frame[sy*48+sx];mode=row['mode']
     expected[i]=src if mode==0 else (expected[i]^src if mode==1 else expected[i]&src if mode==2 else expected[i]|src)
  actual=bytes(row.pop('bytes'));row['match']=actual==expected
  row['sha256']=hashlib.sha256(actual).hexdigest()
 out={'scope':'Original clipped blitter, tile addressing, mode blending and dirty bookkeeping; no replacements; controlled indexed framebuffer','resource':1,'frame':0,'width':96,'height':96,'pitch':104,'guardBytes':128,'rows':rows,'passed':len(rows)==36 and all(row['match'] for row in rows)}
 (ROOT/'analysis/native-scene-sprite-pixels.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print(f"Native PMAPOBJ clipped framebuffer bytes: {sum(row['match'] for row in rows)}/36")
 if not out['passed']:
  print(next(row for row in rows if not row['match']));raise SystemExit(1)
finally:
 device.kill(pid)
 if session:session.detach()
