"""Verify native animation stream allocation/writing with controlled path directions."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base;let nextDirection=0;
 const choose=new NativeCallback(()=>[0,1,65535][nextDirection++],'uint16',['int16','int16','int16','int16'],'mscdecl');
 Interceptor.replace(b.add(0x2836e),choose);Interceptor.flush();
 const generate=new NativeFunction(b.add(0x2869c),'uint',['pointer','int16','uint16'],'mscdecl');
 const obj=Memory.alloc(64),streams=Memory.alloc(32768),map=Memory.alloc(144),rows=[];
 const view=b.add(0xae4c8);view.add(4).writeU32(32768);view.add(12).writePointer(streams);view.add(16).writeU8(1);
 const mv=b.add(0xaeb38);mv.add(4).writeU32(144);mv.add(12).writePointer(map);mv.add(16).writeU8(1);map.writeByteArray(new Uint8Array(144));map.add(2).writeU16(8);map.add(4).writeU16(8);map.add(6).writeU16(1);
 for(const mask of [0,1,3,2147483647,4294967295])for(const endDirection of [-1,2])for(const trim of [0,1,10]){
  obj.writeByteArray(new Uint8Array(64));obj.add(4).writeU16(4);obj.add(6).writeU16(5);obj.add(10).writeU16(1);obj.add(12).writeU16(1);obj.add(0x3c).writeU16(0xaaaa);obj.add(0x3e).writeU16(0xbbbb);
  streams.writeByteArray(new Uint8Array(32768).fill(0xcc));b.add(0x98070).writeU32(mask);nextDirection=0;
  const ret=generate(obj,endDirection,trim),slot=obj.add(0x3c).readU16(),offset=obj.add(0x3e).readU16();
  rows.push({mask,endDirection,trim,retLow:ret&65535,slot,offset,finalMask:b.add(0x98070).readU32(),selectorCalls:nextDirection,bytes:slot<32?Array.from(new Uint8Array(streams.add(slot*1024).readByteArray(5))):[]});
 }
 return rows;
}};''');script.load();rows=script.exports_sync.verify()
 for row in rows:
  slot=next((i for i in range(32) if not row['mask']&(1<<i)),None)
  if slot is None:
   row['match']=(row['retLow']==65535 and row['slot']==0xaaaa and row['offset']==0xbbbb and row['selectorCalls']==0 and row['finalMask']==row['mask'])
  else:
   expected=[0,1]
   if row['endDirection']==-1:
    if row['trim']:expected=expected[:max(0,2-row['trim'])]
   else:expected.append(0x10|row['endDirection'])
   expected.append(239)
   row['match']=(row['slot']==slot and row['offset']==slot*1024 and row['selectorCalls']==3
                 and row['finalMask']==row['mask']|(1<<slot) and row['bytes'][:len(expected)]==expected)
 out={'scope':'Native allocator/generator/bounds/writer; only path-direction selector controlled; return upper bits ignored','rows':rows,'passed':len(rows)==30 and all(row['match'] for row in rows)}
 (ROOT/'analysis/native-generated-animation-stream.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print(f"Native generated animation stream: {sum(row['match'] for row in rows)}/30")
 if not out['passed']:
  print(next(row for row in rows if not row['match']));raise SystemExit(1)
finally:
 device.kill(pid)
 if session:session.detach()
