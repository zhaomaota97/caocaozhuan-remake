"""Verify original scene sprite frame pointer, draw origin and previous-position writeback."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base,obj=Memory.alloc(64),bank=Memory.alloc(0x3c000),keep=[],rows=[];let calls=[];
 const blit=new NativeCallback((x,y,w,h,pixels)=>{calls.push({kind:'blit',x,y,w,h,offset:pixels.sub(bank).toInt32()});},'void',['int','uint','uint','int','pointer'],'mscdecl');
 const dirty=new NativeCallback((x,y,w,h)=>{calls.push({kind:'dirty',x,y,w,h});return 1;},'uint',['uint16','int16','int16','int16'],'mscdecl');
 keep.push(blit,dirty);Interceptor.replace(b.add(0x7e09b),blit);Interceptor.replace(b.add(0x2789d),dirty);Interceptor.flush();
 const draw=new NativeFunction(b.add(0x2a2c4),'void',['pointer','uint16','int16'],'thiscall');
 for(let direction=0;direction<4;direction++)for(let frame=0;frame<20;frame++)for(const x of [24,639,65512])for(const y of [40,104,500]){
  obj.writeByteArray(new Uint8Array(64));obj.add(16).writePointer(bank);obj.add(0x2e).writeU16(direction);obj.add(0x2a).writeU16(frame);obj.add(0x1e).writeU16(111);obj.add(0x20).writeU16(222);calls=[];draw(obj,x,y);
  rows.push({direction,frame,x,y,calls,previousX:obj.add(0x22).readU16(),previousY:obj.add(0x24).readU16(),currentX:obj.add(0x1e).readU16(),currentY:obj.add(0x20).readU16()});
 }
 return rows;
}};''');script.load();rows=script.exports_sync.verify()
 for row in rows:
  top=(row['y']-64)&65535
  expected=[dict(kind='blit',x=row['x'] if row['x']<32768 else row['x']-65535,y=top,w=48,h=64,offset=(row['direction']*20+row['frame'])*3072),
            dict(kind='dirty',x=row['x'],y=top if top<32768 else top-65536,w=48,h=64)]
  row['match']=(row['calls']==expected and row['previousX']==111 and row['previousY']==222 and row['currentX']==row['x'] and row['currentY']==top)
 out={'scope':'Original scene draw entry, pointer getter and position writeback; blitter and dirty-region leaf recorded; no final framebuffer tested','rows':rows,'passed':len(rows)==720 and all(row['match'] for row in rows)}
 (ROOT/'analysis/native-scene-sprite-draw-dispatch.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print(f"Native scene sprite draw dispatch: {sum(row['match'] for row in rows)}/720")
 if not out['passed']:
  print(next(row for row in rows if not row['match']));raise SystemExit(1)
finally:
 device.kill(pid)
 if session:session.detach()
