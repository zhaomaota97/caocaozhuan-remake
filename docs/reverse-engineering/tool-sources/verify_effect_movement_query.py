"""Execute native effect movement bounds and collision using a controlled map view."""
import json
from pathlib import Path
import struct
import frida
import pefile
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base,query=new NativeFunction(b.add(0x2830a),'uint',['pointer','pointer','int16','int16','uint16'],'mscdecl');
 const data=Memory.alloc(144),view=b.add(0xaeb38),xptr=Memory.alloc(2),yptr=Memory.alloc(2),rows=[];
 view.add(4).writeU32(144);view.add(12).writePointer(data);view.add(16).writeU8(1);
 for(const blocked of [false,true]){
  data.writeByteArray(new Uint8Array(144));data.add(2).writeU16(8);data.add(4).writeU16(8);data.add(6).writeU16(1);
  if(blocked)data.add(16+(4*8+4)*2).writeU16(0xf001);
  for(const [width,height] of [[1,1],[2,2],[3,3]])for(let y=0;y<8;y++)for(let x=0;x<8;x++)for(let direction=0;direction<8;direction++){
   xptr.writeS16(x);yptr.writeS16(y);const ret=query(xptr,yptr,width,height,direction)&65535;
   rows.push({blocked,width,height,x,y,direction,ret,finalX:xptr.readS16(),finalY:yptr.readS16()});
  }
 }
 return rows;
}};''');script.load();rows=script.exports_sync.verify()
 pe=pefile.PE(str(ROOT/'Ekd5.exe'));dy=struct.unpack('<8h',pe.get_data(0x8b8b0,16));dx=struct.unpack('<8h',pe.get_data(0x8b8c0,16))
 for row in rows:
  nx=row['x']+dx[row['direction']];ny=row['y']+dy[row['direction']];h=row['height'];w=row['width'];top=ny-h+1
  inside=(0<=nx<8 and 0<=nx+w-1<8 and 0<=top<8 and 0<=top-h+1<8)
  collision=(ny>=8 or (row['blocked'] and nx<=4<nx+w and top<=4<=ny)) if inside else False
  ret=0 if inside and not collision else 65535
  row['match']=(row['ret']==ret and row['finalX']==(nx if inside else row['x']) and row['finalY']==(ny if inside else row['y']))
 out={'scope':'Native movement query, bounds, tile lookup and collision scan; synthetic map view; no replacements','dx':dx,'dy':dy,'rows':rows,'passed':len(rows)==3072 and all(row['match'] for row in rows)}
 (ROOT/'analysis/native-effect-movement-query.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print(f"Native effect movement bounds/collision: {sum(row['match'] for row in rows)}/3072")
 if not out['passed']:
  print(next(row for row in rows if not row['match']));raise SystemExit(1)
finally:
 device.kill(pid)
 if session:session.detach()
