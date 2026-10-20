"""Reuse the saved-battle native initialization, then probe original path reconstruction."""
import ast
import json
import sys
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]
tree = ast.parse((ROOT/'tools/export_slot08_native_health.py').read_text(encoding='utf-8'))
scripts = [node.args[0].value for node in ast.walk(tree)
           if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
           and node.func.attr == 'create_script' and isinstance(node.args[0], ast.Constant)]
if len(scripts) != 1 or scripts[0].count('return out;') != 1:
    raise RuntimeError('Native initialization changed; review harness extraction')
script_source = scripts[0].replace('return out;', '''
 const pathFunction=new NativeFunction(b.add(0x37e2e),'pointer',
   ['pointer','pointer','pointer','uint8','uint8'],'thiscall');
 const paths=[];
 for(const row of out){
  const a=b.add(0xb2c50+row.slot*36);
  search(a,a.add(6),row.move,0,255,255,1);
  const start=[a.add(6).readU8(),a.add(7).readU8()];
  for(let index=0;index<640;index++){
   const cost=row.nativeMovementCosts[index];
   if(cost===255 || cost===0)continue;
   const target=[index%20,Math.floor(index/20)];
   if(battlefield.add(0xc80+index).readU8()!==255)continue;
   coordinate.writeU8(target[0]);coordinate.add(1).writeU8(target[1]);
   battlefield.add(0x1900).writeByteArray(new Uint8Array(640).fill(255));
   const path=pathFunction(a,a.add(6),coordinate,255,0);
   const directions=[];let x=start[0],y=start[1];
   for(let step=0;step<640 && (x!==target[0] || y!==target[1]);step++){
    const direction=path.add(step).readU8();directions.push(direction);
    if(direction>3)break;
    x+=[0,1,0,-1][direction];y+=[-1,0,1,0][direction];
   }
   paths.push({slot:row.slot,start,target,cost,directions,end:[x,y],
     actorUnchanged:a.add(6).readU8()===start[0] && a.add(7).readU8()===start[1]});
  }
 }
 return paths;
''')
player_mode = '--player' in sys.argv
permissions_mode = '--permissions' in sys.argv
actions_mode = '--actions' in sys.argv
player_mode = player_mode or permissions_mode or actions_mode
commit_mode = '--commit' in sys.argv or player_mode
if commit_mode:
    script_source = script_source.replace('return paths;', '''
 const callbacks=[];
 function sink(rva,args,abi,fn){
  const callback=new NativeCallback(fn || (()=>{}),'void',args,abi);
  callbacks.push(callback);Interceptor.replace(b.add(rva),callback);
 }
 let steps=[];
 sink(0x41488,['pointer','int','uint','uint'],'thiscall');
 sink(0x4201b,['pointer','uint8'],'thiscall',(actor,direction)=>{
  steps.push({x:actor.add(6).readU8(),y:actor.add(7).readU8(),direction});
 });
 sink(0x3fcc9,['pointer'],'fastcall');
 sink(0x4a88a,['pointer'],'fastcall');
 Interceptor.flush();
 const commit=new NativeFunction(b.add(0x3a956),'void',['pointer'],'fastcall');
 const occupancy=new Uint8Array(battlefield.add(0xc80).readByteArray(640));
 const committed=[];
 for(const path of paths){
  const a=b.add(0xb2c50+path.slot*36);
  const snapshot=new Uint8Array(a.readByteArray(36));
  a.add(13).writeU8(snapshot[13]&~0x80);
  search(a,a.add(6),out.find(row=>row.slot===path.slot).move,0,255,255,1);
  b.add(0xb2c20).writeU8(path.target[0]);b.add(0xb2c21).writeU8(path.target[1]);
  steps=[];const returned=commit(a);
  committed.push({slot:path.slot,start:path.start,target:path.target,
   end:[a.add(6).readU8(),a.add(7).readU8()],steps,
   expectedDirections:path.directions,returned,flagsBefore:snapshot[13]&~0x80,flagsAfter:a.add(13).readU8(),
   oldOccupant:battlefield.add(0xc80+path.start[1]*20+path.start[0]).readU8(),
   newOccupant:battlefield.add(0xc80+path.target[1]*20+path.target[0]).readU8(),
   bytesBefore:Array.from(snapshot),bytesAfter:Array.from(new Uint8Array(a.readByteArray(36)))});
  a.writeByteArray(snapshot);battlefield.add(0xc80).writeByteArray(occupancy);
 }
 return committed;
''')
if player_mode:
    script_source = script_source.replace("const commit=new NativeFunction(b.add(0x3a956),'void'",
                                         "const commit=new NativeFunction(b.add(0x3d538),'uint'")
    script_source = script_source.replace('const occupancy=new Uint8Array', '''
 let click=[255,255],inputCalls=0;
 const inputCoordinate=Memory.alloc(2);
 const inputCallback=new NativeCallback((self)=>{
  inputCalls++;if(inputCalls>2)throw new Error('Unexpected input loop');
  const current=inputCalls===1 ? click : [255,255];
  inputCoordinate.writeU8(current[0]);inputCoordinate.add(1).writeU8(current[1]);return inputCoordinate;
 },'pointer',['pointer'],'fastcall');
 callbacks.push(inputCallback);Interceptor.replace(b.add(0x5418f),inputCallback);
 sink(0x539dc,['pointer','uint','uint8','int'],'thiscall');
 sink(0x53b13,['pointer'],'fastcall');sink(0x7467a,['pointer','int','int'],'thiscall');
 sink(0x2f699,['uint'],'mscdecl');
 Interceptor.flush();
 b.add(0xb4230).writeU8(4);
 for(const row of out){
  const a=b.add(0xb2c50+row.slot*36),start=[a.add(6).readU8(),a.add(7).readU8()];
  paths.push({slot:row.slot,start,target:start,directions:[],mode:'self'});
  paths.push({slot:row.slot,start,target:[255,255],directions:[],mode:'cancel'});
 }
 const occupancy=new Uint8Array''')
    script_source = script_source.replace('a.add(13).writeU8(snapshot[13]&~0x80);', '''
  a.add(13).writeU8(snapshot[13]&~0x82);a.add(14).writeU8(7);a.add(30).writeU8(snapshot[30]&~8);
  const normalized=new Uint8Array(a.readByteArray(36));
  click=path.target;inputCalls=0;''')
    script_source = script_source.replace('committed.push({slot:path.slot,',
                                         "committed.push({mode:path.mode || 'move',inputCalls,slot:path.slot,")
    script_source = script_source.replace('flagsBefore:snapshot[13]&~0x80', 'flagsBefore:normalized[13]')
    script_source = script_source.replace('bytesBefore:Array.from(snapshot)', 'bytesBefore:Array.from(normalized)')
    # Cancel has no valid target-cell occupancy; do not read outside the map.
    script_source = script_source.replace('newOccupant:battlefield.add(0xc80+path.target[1]*20+path.target[0]).readU8()',
        "newOccupant:path.mode==='cancel' ? null : battlefield.add(0xc80+path.target[1]*20+path.target[0]).readU8()")
if permissions_mode:
    script_source = script_source.replace('const occupancy=new Uint8Array', '''
 for(const row of out){
  const a=b.add(0xb2c50+row.slot*36),start=[a.add(6).readU8(),a.add(7).readU8()];
  for(const mode of ['blocked-flag2','blocked-flag128','blocked-status8','blocked-control']){
   paths.push({slot:row.slot,start,target:start,directions:[],mode});
  }
  const other=out.find(unit=>unit.slot!==row.slot),o=b.add(0xb2c50+other.slot*36);
  paths.push({slot:row.slot,start,target:[o.add(6).readU8(),o.add(7).readU8()],directions:[],mode:'invalid-occupied'});
 }
 const occupancy=new Uint8Array''',1)
    script_source = script_source.replace('const normalized=new Uint8Array', '''
  b.add(0xb4230).writeU8(4);
  if(path.mode==='blocked-flag2')a.add(13).writeU8(a.add(13).readU8()|2);
  if(path.mode==='blocked-status8')a.add(30).writeU8(a.add(30).readU8()|8);
  if(path.mode==='blocked-flag128'){
   a.add(13).writeU8(a.add(13).readU8()|128);b.add(0xb4230).writeU8(0);
  }
  if(path.mode==='blocked-control'){a.add(14).writeU8(0);b.add(0xb4230).writeU8(0);}
  const normalized=new Uint8Array''',1)
if actions_mode:
    script_source = script_source.replace("const commit=new NativeFunction(b.add(0x3d538),'uint'",
                                         "const commit=new NativeFunction(b.add(0x3dde3),'uint'")
    script_source = script_source.replace('const occupancy=new Uint8Array', '''
 const originalPaths=paths.filter(path=>!path.mode);paths.length=0;
 for(const path of originalPaths)for(const action of [255,4])paths.push({...path,action});
 let action=255,actionCalls=0;
 const actionCallback=new NativeCallback(()=>{
  if(++actionCalls>1)throw new Error('Unexpected action loop');return action;
 },'uint8',[],'mscdecl');
 callbacks.push(actionCallback);Interceptor.replace(b.add(0x5e69a),actionCallback);
 sink(0x53e32,['pointer'],'fastcall');sink(0x5bba0,['pointer','uint8','uint8'],'thiscall');
 sink(0x5137c,['int','int','uint','uint','uint','pointer'],'mscdecl');
 sink(0x1e5db,[],'mscdecl');sink(0x1e5f6,[],'mscdecl');sink(0x2c4e0,[],'mscdecl');
 const availabilityCallback=new NativeCallback(()=>0,'uint8',['uint','uint8','uint8'],'mscdecl');
 callbacks.push(availabilityCallback);Interceptor.replace(b.add(0x3e273),availabilityCallback);
 const configCallback=new NativeCallback(()=>0,'uint',['pointer'],'fastcall');
 callbacks.push(configCallback);Interceptor.replace(b.add(0xd9ee),configCallback);
 // Real mirror implementation needs writable sprite and scratch views.
 const pixels=Memory.alloc(115*0x6300),scratch=Memory.alloc(0x1200);
 for(const [rva,p,size] of [[0xaab80,pixels,115*0x6300],[0xaf490,scratch,0x1200]]){
  const v=b.add(rva);v.add(4).writeU32(size);v.add(12).writePointer(p);v.add(16).writeU8(1);
 }
 const flip=new NativeFunction(b.add(0x3fd34),'void',['pointer','int'],'thiscall');
 Interceptor.revert(b.add(0x4201b));
 Interceptor.flush();
 sink(0x4201b,['pointer','uint8'],'thiscall',(actor,direction)=>{
  steps.push({x:actor.add(6).readU8(),y:actor.add(7).readU8(),direction});
  actor.add(15).writeU8(direction);
  if(direction===1 || direction===3)flip(actor,direction===1 ? 1 : 0);
 });
 Interceptor.flush();
 Process.setExceptionHandler(details=>{
  send({exception:details.type,address:details.address.toString(),
   instruction:Instruction.parse(details.context.pc).toString(),
   backtrace:Thread.backtrace(details.context,Backtracer.ACCURATE).map(DebugSymbol.fromAddress).map(String)});
  return false;
 });
 const occupancy=new Uint8Array''',1)
    script_source = script_source.replace('const normalized=new Uint8Array', '''
  a.add(13).writeU8(a.add(13).readU8()&~4);action=path.action;actionCalls=0;
  const normalized=new Uint8Array''',1)
    script_source = script_source.replace("committed.push({mode:path.mode || 'move',",
                                         "committed.push({action,actionCalls,mode:path.mode || 'move',")
    script_source = script_source.replace('steps=[];const returned=commit(a);', '''
  steps=[];let returned;
  try{returned=commit(a);}catch(error){
   send({nativeError:String(error),context:error.context,properties:Object.getOwnPropertyNames(error)});throw error;
  }''')
data = dict(entries(ROOT/'Data.e5'))
device = frida.get_local_device()
pid = device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')], cwd=str(ROOT/'analysis/runtime-game'))
session = None
try:
    session = device.attach(pid)
    script = session.create_script(script_source)
    script.on('message',lambda message,data: print(message) if message.get('type')=='send' else None)
    script.load()
    rows = script.exports_sync.read(list(data[0]), list(data[1]), list(data[3]), list(data[4]),
        list((ROOT/'Sv08d.e5s').read_bytes()[0x14dc:]),
        list((ROOT/'Sv08s.e5s').read_bytes()[1301:4291]),
        list((ROOT/'analysis/saved-battlefields/Sv08s-terrain.bin').read_bytes()))
    if commit_mode:
        for row in rows:
            expected_bytes = row['bytesBefore'].copy()
            expected_bytes[6:8] = row['target']
            expected_bytes[13] = row['flagsBefore'] | 4
            row['match'] = (row['end'] == row['target'] and row['oldOccupant'] == 255
                and row['newOccupant'] == row['slot']
                and row['flagsAfter'] == row['flagsBefore'] | 4
                and [step['direction'] for step in row['steps']] == row['expectedDirections']
                and row['bytesAfter'] == expected_bytes)
            if player_mode:
                if row['mode']!='move':
                    row['match'] = (row['end']==row['start'] and row['bytesAfter']==row['bytesBefore']
                        and not row['steps'] and row['oldOccupant']==row['slot'])
                expected_return = 1 if row['mode'] in ('move','self') else 0
                expected_inputs = 2 if row['mode']=='invalid-occupied' else 1
                row['match'] = row['match'] and row['inputCalls']==expected_inputs and row['returned']==expected_return
            if actions_mode:
                expected_bytes = row['bytesBefore'].copy()
                flags = expected_bytes[13]
                direction = expected_bytes[15]
                for step in row['steps']:
                    direction = step['direction']
                    if direction==1:
                        flags |= 8
                    elif direction==3:
                        flags &= ~8
                if row['action']==255:
                    direction = expected_bytes[15]
                    if direction==1:
                        flags |= 8
                    elif direction==3:
                        flags &= ~8
                    expected_position = row['start']
                    expected_return, old_occupant, new_occupant = 0,row['slot'],255
                else:
                    flags |= 6
                    expected_position = row['target']
                    expected_return, old_occupant, new_occupant = 1,255,row['slot']
                expected_bytes[6:8] = expected_position
                expected_bytes[13],expected_bytes[15] = flags,direction
                row['match'] = (row['returned']==expected_return and row['end']==expected_position
                    and row['bytesAfter']==expected_bytes and row['oldOccupant']==old_occupant
                    and row['newOccupant']==new_occupant and row['inputCalls']==1 and row['actionCalls']==1
                    and [step['direction'] for step in row['steps']]==row['expectedDirections'])
        matched = sum(row['match'] for row in rows)
    else:
        matched = sum(row['end'] == row['target'] and row['actorUnchanged'] for row in rows)
    result = {'function':'0x43D538' if player_mode else '0x43A956' if commit_mode else '0x437E2E','budget':255,'fallback':0,
              'replacedFunctions': ['0x441488','0x44201B','0x43FCC9','0x44A88A'] if commit_mode else [],
              'total':len(rows),'matched':matched,'rows':rows}
    if player_mode:
        result['scope'] = 'controlled click; actor flags 0x82 cleared, AI mode 7, status bit 8 cleared, global control bit 4 set'
        result['replacedFunctions'] += ['0x45418F','0x4539DC','0x453B13','0x47467A','0x42F699']
    if permissions_mode:
        result['scope'] += '; additional permission flags/control variants and occupied-click then cancel'
    if actions_mode:
        result['function'] = '0x43DDE3'
        result['scope'] += '; post-move actions 255 and 4; availability UI predicates replaced; mirror implementation retained'
        result['replacedFunctions'] += ['0x45E69A','0x453E32','0x45BBA0','0x43E273','0x40D9EE',
                                        '0x45137C','0x41E5DB','0x41E5F6','0x42C4E0']
    name = 'native-player-movement-actions.json' if actions_mode else 'native-player-movement-permissions.json' if permissions_mode else 'native-player-movement.json' if player_mode else 'native-movement-commit.json' if commit_mode else 'native-movement-paths.json'
    (ROOT/'analysis'/name).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f"Native {'movement commits' if commit_mode else 'reconstructed paths'}: {matched}/{len(rows)}")
    if not rows or matched != len(rows):
        raise SystemExit('Path probe mismatch; inspect output')
finally:
    device.kill(pid)
    if session:
        session.detach()
