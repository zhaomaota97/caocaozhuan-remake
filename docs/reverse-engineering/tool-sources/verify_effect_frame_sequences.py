"""Verify native nine-byte frame sequences and movement-success commit behavior."""
import json
from pathlib import Path
import frida
import pefile
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base;let success=false;
 const move=new NativeCallback((x,y,_w,_h,_direction)=>{x.writeU16(11);y.writeU16(22);return success?0:65535;},'uint',['pointer','pointer','int16','int16','uint16'],'mscdecl');
 Interceptor.replace(b.add(0x2830a),move);Interceptor.flush();
 const bind=new NativeFunction(b.add(0x2a4b0),'void',['pointer','uint16'],'thiscall');
 const step=new NativeFunction(b.add(0x2a4f5),'uint8',['pointer','uint16'],'thiscall');
 const obj=Memory.alloc(64),rows=[];
 for(let sequence=0;sequence<19;sequence++)for(const canMove of [false,true]){
  obj.writeByteArray(new Uint8Array(64));obj.add(4).writeU16(4);obj.add(6).writeU16(5);obj.add(0x2e).writeU16(7);bind(obj,sequence);success=canMove;
  for(let tick=1;tick<=10;tick++){
   const ret=step(obj,2);rows.push({sequence,canMove,tick,ret,index:obj.add(0x1a).readU16(),frame:obj.add(0x2a).readU16(),x:obj.add(4).readU16(),y:obj.add(6).readU16(),direction:obj.add(0x2e).readU16()});
  }
 }
 return rows;
}};''');script.load();rows=script.exports_sync.verify()
 pe=pefile.PE(str(ROOT/'Ekd5.exe'));raw=pe.get_data(0x8b920,19*9)
 for row in rows:
  definition=raw[row['sequence']*9:(row['sequence']+1)*9];length=definition[0]
  index=row['tick']%length if length else 0
  expected_pos=(11,22,2) if row['canMove'] else (4,5,7)
  row['match']=(row['index']==index and row['frame']==definition[1+index] and row['ret']==int(row['canMove']) and (row['x'],row['y'],row['direction'])==expected_pos)
 out={'scope':'Original binder and frame step; movement query controlled; no rendering tested','definitions':[raw[i*9:(i+1)*9].hex() for i in range(19)],'rows':rows,'passed':len(rows)==380 and all(row['match'] for row in rows)}
 (ROOT/'analysis/native-effect-frame-sequences.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print(f"Native effect frame sequence and movement commit: {sum(row['match'] for row in rows)}/{len(rows)}")
 if not out['passed']:
  print(next(row for row in rows if not row['match']));raise SystemExit(1)
finally:
 device.kill(pid)
 if session:session.detach()
