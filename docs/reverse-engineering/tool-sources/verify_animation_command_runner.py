"""Compare native animation command scheduling against an independent state model."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base;let moves=[];
 Interceptor.attach(b.add(0x2830a),{onEnter(args){moves.push(args[4].toUInt32()&65535);}});Interceptor.flush();
 const run=new NativeFunction(b.add(0x2a361),'uint',['pointer'],'fastcall');
 const bind=new NativeFunction(b.add(0x2a4b0),'void',['pointer','uint16'],'thiscall');
 const obj=Memory.alloc(64),input=Memory.alloc(512),view=b.add(0xae4c8),rows=[];
 view.add(4).writeU32(512);view.add(12).writePointer(input);view.add(16).writeU8(1);
 const map=Memory.alloc(144),mapView=b.add(0xaeb38);mapView.add(4).writeU32(144);mapView.add(12).writePointer(map);mapView.add(16).writeU8(1);
 for(const blocked of [false,true])for(const stream of [[0,1,239],[16,18,239],[224,7,0,239],[239]])for(const interval of [0,1,3]){
  map.writeByteArray(new Uint8Array(144));map.add(2).writeU16(8);map.add(4).writeU16(8);map.add(6).writeU16(1);if(blocked)map.add(16+(4*8+5)*2).writeU16(0xf001);
  obj.writeByteArray(new Uint8Array(64));obj.writeU16(interval);obj.add(4).writeU16(4);obj.add(6).writeU16(5);obj.add(10).writeU16(1);obj.add(12).writeU16(1);obj.add(0x2e).writeU16(7);bind(obj,0);input.writeByteArray(stream);
  for(let tick=1;tick<=20;tick++){
   moves=[];const status=run(obj)&65535;
   rows.push({blocked,stream,interval,tick,status,counter:obj.add(2).readU16(),offset:obj.add(0x3e).readU16(),index:obj.add(0x1a).readU16(),frame:obj.add(0x2a).readU16(),direction:obj.add(0x2e).readU16(),x:obj.add(4).readU16(),y:obj.add(6).readU16(),moves});
  }
 }
 return rows;
}};''');script.load();rows=script.exports_sync.verify()
 state=None
 for row in rows:
  if row['tick']==1:state=dict(counter=0,offset=0,index=0,frame=0,direction=7,x=4,y=5)
  status=0;moves=[]
  if state['counter']<row['interval']:state['counter']+=1
  else:
   state['counter']=0;cmd=row['stream'][state['offset']]
   if cmd==239:status=65535
   else:
    if cmd<16:
     moves=[cmd&15];state['index']=(state['index']+1)%4;state['frame']=[0,1,0,2][state['index']]
     dx=[0,1,0,-1,0,-1,1,0][cmd&15];dy=[-1,0,1,0,0,-1,1,0][cmd&15]
     nx,ny=state['x']+dx,state['y']+dy
     if 0<=nx<8 and 0<=ny<8 and not(row['blocked'] and (nx,ny)==(5,4)):
      state.update(x=nx,y=ny,direction=cmd&15)
    elif cmd<32:state['direction']=cmd&15
    state['offset']+=2 if cmd==224 else 1
    if row['stream'][state['offset']]==239:status=65535
  row['match']=(all(row[key]==value for key,value in state.items()) and row['status']==status and row['moves']==moves)
 out={'scope':'Original command runner, reader, binder, stepper, bounds, collision and linear views; no function replacements; controlled map/stream','rows':rows,'passed':len(rows)==480 and all(row['match'] for row in rows)}
 (ROOT/'analysis/native-animation-command-runner.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print(f"Native animation runner with real movement and collision: {sum(row['match'] for row in rows)}/480")
 if not out['passed']:
  print(next(row for row in rows if not row['match']));raise SystemExit(1)
finally:
 device.kill(pid)
 if session:session.detach()
