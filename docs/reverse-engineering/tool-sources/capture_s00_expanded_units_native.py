"""Expand S_00 scene records using real DATA tables and native unit rules."""
import argparse
import json
import struct
from pathlib import Path
import frida
from export_map_layouts import entries
from export_eex_bodies import encode_instruction,encode_block
from export_story_readable import walk

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--placement',action='store_true',help='execute native coordinate entry on actual map0 terrain')
    parser.add_argument('--appearances',action='store_true',help='probe opcode76 handlers after placement; does not execute story conditions')
    parser.add_argument('--liu-event',action='store_true',help='execute actual Liu/Guan/Zhang branch; capture presentation and scripted-move requests')
    parser.add_argument('--liu-movement',action='store_true',help='execute native path search and coordinate stepping for Liu event; AI prepass bypassed')
    parser.add_argument('--victory-event',action='store_true',help='probe original full branch9 with living allies, captured movement requests and supplied death flags')
    parser.add_argument('--victory-movement',action='store_true',help='execute native path core for all six victory movements; AI prepass and drawing suppressed')
    parser.add_argument('--fallen-ally',type=int,choices=(32,3,33),help='victory fixture: set matching death flag and remove this ally with native code')
    args=parser.parse_args()
    if args.liu_movement:args.liu_event=True
    if args.victory_movement:args.victory_event=True
    if args.fallen_ally is not None:args.victory_event=True
    if args.appearances:args.placement=True
    if args.liu_event:args.placement=True
    if args.victory_event:args.placement=True
    event_file=[]
    if args.liu_event or args.victory_event:
        number=9 if args.victory_event else 1
        branch=next(b for b in json.loads((ROOT/'analysis/eex-bodies/S_00.json').read_text(encoding='utf-8')) if b['segment']==1 and b['branch']==number)
        body=encode_block(branch)
        raw=(ROOT/'S_00.eex').read_bytes()
        start,end,predicate_start=(13169,14333,13119) if args.victory_event else (7885,8353,7846)
        if body!=raw[start:end]:raise ValueError('Event body differs from original')
        predicate=raw[predicate_start:start-2]
        payload=predicate+struct.pack('<H',len(body))+body
        event_file=list(b'EEX\0\1\2\0\0\0\0'+struct.pack('<I',14)+struct.pack('<HH',1,len(payload))+payload)
    appearance_cases=[]
    if args.appearances:
        predicates=json.loads((ROOT/'analysis/eex-predicates/S_00.json').read_text(encoding='utf-8'))
        for branch in json.loads((ROOT/'analysis/eex-bodies/S_00.json').read_text(encoding='utf-8')):
            for node,conditions in walk(branch['nodes']):
                if node['opcode']==76:
                    predicate=next(p['instructions'] for p in predicates if p['segment']==branch['segment'] and p['branch']==branch['branch'])
                    appearance_cases.append(dict(offset=node['offset'],segment=branch['segment'],branch=branch['branch'],
                                                 predicates=predicate,nested_conditions=conditions,bytes=list(encode_instruction(node))))
    data=dict(entries(ROOT/'Data.e5'))
    replay=json.loads((ROOT/'analysis/native-s00-unit-setup-replay.json').read_text())
    snapshot=next(r['state_after'] for r in reversed(replay['rows']) if r.get('state_after'))
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={capture(data,snapshot,placement,terrain,appearances,eventFile,nativeMovement,victory,fallenAlly,mapSize=[20,20]){
 const b=Process.mainModule.base,keep=[],moves=[];
 function buffer(bytes){const p=Memory.alloc(bytes.length);p.writeByteArray(bytes);return p;}
 const source=buffer(data[0]);
 function replace(rva,ret,args,abi,fn){const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);Interceptor.replace(b.add(rva),cb);}
 replace(0x81100,'int',['pointer'],'mscdecl',()=>0);
 replace(0x0E090,'pointer',['pointer'],'fastcall',()=>source);
 replace(0x1B51E,'uint',['pointer','int','pointer'],'mscdecl',()=>1);
 if(!placement)replace(0x42B03,'uint',['pointer','uint8','uint8','int','int'],'thiscall',(slot,x,y,flag8,flag4)=>{
  moves.push({slot:slot.sub(b.add(0xB2C50)).toInt32()/36,x,y,flag8,flag4});return 1;
 });
 if(placement){
  const set=new NativeFunction(b.add(0x42718),'void',['pointer','uint8'],'thiscall');
  const clear=new NativeFunction(b.add(0x06690),'void',['pointer','uint8'],'thiscall');
  replace(0x3FD34,'void',['pointer','int'],'thiscall',(slot,flip)=>{if(flip)set(slot,8);else clear(slot,8);});
  replace(0x3FCC9,'void',['int'],'fastcall',()=>{});
 }
 if(appearances.length||eventFile.length){
  replace(0x5503F,'void',['pointer','uint8','uint8'],'thiscall',()=>{});
  replace(0x7467A,'void',['pointer','uint','int'],'thiscall',()=>{});
  replace(0x4A88A,'void',['int'],'fastcall',()=>{});
  replace(0x03340,'void',['pointer','int'],'thiscall',()=>{});
  replace(0x2C4E0,'void',[],'mscdecl',()=>{});
  if(victory){
   replace(0x419B6,'void',['pointer','int8'],'thiscall',()=>{});
   replace(0x53B13,'void',['pointer'],'thiscall',()=>{});
   replace(0x54F10,'void',['pointer','uint','int'],'thiscall',()=>{});
  }
 }
 const eventCalls=[];
 if(victory)replace(0x4B5A8,'void',['int','pointer','uint'],'mscdecl',(money,items,mode)=>eventCalls.push({kind:'reward-display',money,items:Array.from(new Uint8Array(items.readByteArray(3))),mode}));
 if(eventFile.length){
  function textBytes(p){const out=[];for(let i=0;i<2048;i++){const x=p.add(i).readU8();if(!x)break;out.push(x);}return out;}
  replace(0x5965D,'void',['pointer','uint'],'mscdecl',(text,speaker)=>eventCalls.push({kind:'dialogue',speaker,bytes:textBytes(text)}));
  replace(0x2D5F1,'void',['pointer','uint','uint'],'mscdecl',(text,speaker,style)=>eventCalls.push({kind:'plain',speaker,style,bytes:textBytes(text)}));
  replace(0x57428,'uint',['uint','uint','uint8','uint','uint','uint'],'mscdecl',(a,t,d,p0,p1,p2)=>{eventCalls.push({kind:'orient',actor:a,target:t,direction:d,options:[p0,p1,p2]});return 1;});
  if(!nativeMovement)replace(0x59487,'uint',['int','uint8','uint8','uint'],'mscdecl',(actor,x,y,d)=>{eventCalls.push({kind:'move-request',actor,x,y,direction:d});return 1;});
  if(nativeMovement){
   const search=new NativeFunction(b.add(0x38308),'uint8',['pointer','pointer','uint','uint','uint','uint','int'],'thiscall');
   const advance=new NativeFunction(b.add(0x3A956),'void',['pointer'],'fastcall');
   const paths=[];
   replace(0x4201B,'void',['pointer','uint8'],'thiscall',(slot,direction)=>{
    paths.push({actor:slot.readU32(),from:[slot.add(6).readU8(),slot.add(7).readU8()],direction});
    if(paths.length>1000)throw new Error('Path step limit exceeded');
   });
   replace(0x35829,'void',['uint8','uint8'],'mscdecl',()=>{});
   replace(0x3AD1C,'void',['pointer'],'fastcall',(slot)=>{
    const start=paths.length,x=slot.add(9).readU8(),y=slot.add(10).readU8();
    const status=search(slot,slot.add(6),255,2,x,y,1);
    b.add(0xB2C20).writeByteArray([x,y]);
    if(status===1)advance(slot);
    eventCalls.push({kind:'native-path',actor:slot.readU32(),search:status,target:[x,y],
      position:[slot.add(6).readU8(),slot.add(7).readU8()],steps:paths.slice(start)});
   });
  }
 }
 replace(0x79A01,'void',['uint'],'mscdecl',()=>{});
 replace(0x59D8B,'uint',['int','uint8','int','uint8','uint8'],'mscdecl',()=>1);
 Interceptor.flush();
 const expand=new NativeFunction(b.add(0x08BE3),'pointer',['pointer','uint16','pointer','int'],'thiscall');
 const loadItem=new NativeFunction(b.add(0x0C537),'pointer',['pointer','pointer'],'thiscall');
 const loadClass=new NativeFunction(b.add(0x093EF),'pointer',['pointer','pointer'],'thiscall');
 for(let i=0;i<512;i++)expand(b.add(0xA1B68+i*72),i,source.add(i*32),0);
 const items=buffer(data[1]);for(let i=0;i<104;i++)loadItem(b.add(0xA1140+i*25),items.add(i*25));
 let classes=buffer(data[3]);for(let i=0;i<53;i++)classes=loadClass(b.add(0xABFA0+i*27),classes);
 b.add(0xAE4E0).writeByteArray(data[4]);
 if(placement){
  const pixels=Memory.alloc(0x3000);pixels.writeByteArray(new Uint8Array(0x3000));
  pixels.add(0x640).writeByteArray(terrain);pixels.add(0xC80).writeByteArray(new Uint8Array(1600).fill(255));
  const view=b.add(0xAEB38);view.add(4).writeU32(0x3000);view.add(12).writePointer(pixels);view.add(16).writeU8(1);
  const cost=Memory.alloc(0x3000);cost.writeByteArray(new Uint8Array(0x3000));
  const costView=b.add(0xAAB68);costView.add(4).writeU32(0x3000);costView.add(12).writePointer(cost);costView.add(16).writeU8(1);
  b.add(0xB422C).writeU8(mapSize[0]);b.add(0xB422D).writeU8(mapSize[1]);b.add(0xB2C48).writeU32(1);
 }
 b.add(0x92F90).writeByteArray(snapshot);
 const initialize=new NativeFunction(b.add(0x42613),'void',['pointer','uint8'],'thiscall');
 for(let i=0;i<115;i++)initialize(b.add(0xB2C50+i*36),i);
 new NativeFunction(b.add(0x4CC85),'void',[],'mscdecl')();
 const appearanceResults=[];
 let eventExecution=null;
 if(eventFile.length){
  b.add(0xAC63C).writeU8(3);b.add(0xB3D0A).writeU8(0);b.add(0xB3D18).writeU8(2);
  if(victory){
   const appear=new NativeFunction(b.add(0x570EE),'uint',['int'],'mscdecl');
   for(const id of [0,32,3,33,258,259,157])appear(id);
   if(fallenAlly!==null){
    new NativeFunction(b.add(0x5A7B7),'uint',['int','int','int'],'mscdecl')(fallenAlly,0,1);
   }
   b.add(0xB0770+12).writeU32(0);
  }
  const input=buffer(eventFile),obj=Memory.alloc(0x2040);obj.writeByteArray(new Uint8Array(0x2040));
  obj.writePointer(b.add(0x86610));obj.add(16).writeU16(65535);obj.add(20).writeS32(-1);
  obj.add(32).writePointer(input);obj.add(40).writeU32(1);obj.add(48).writeU32(10);
  if(victory)for(const flag of [50,51])obj.add(0x38+flag*4).writeU32(1);
  if(fallenAlly!==null)obj.add(0x38+({32:52,3:53,33:54}[fallenAlly])*4).writeU32(1);
  const select=new NativeFunction(b.add(0x100A1),'uint',['pointer'],'fastcall');
  const execute=new NativeFunction(b.add(0x1084E),'int',['pointer','int','int'],'thiscall');
  let lastOpcode=null;
  if(victory)Interceptor.attach(b.add(0x109EF),{onEnter(){lastOpcode=this.context.ecx.add(12).readPointer().readU16();}});
  const selected=select(obj);let result=null;
  try{result=selected?execute(obj,1,0):null;}catch(e){throw new Error('Event stopped at opcode '+lastOpcode+': '+e+'; calls='+JSON.stringify(eventCalls));}
  const flag11=obj.add(0x38+11*4).readU32();
  obj.add(4).writeU32(0);obj.add(8).writeU32(0);obj.add(16).writeU16(65535);
  obj.add(20).writeS32(-1);obj.add(40).writeU32(1);
  const selectedAgain=select(obj);
  eventExecution={selected,result,flag11,selectedAgain,calls:eventCalls,
   money:b.add(0xB0770+12).readU32(),battleState:b.add(0xB3D08+1).readU8(),
   completionFlags:[0,100,600].map(i=>obj.add(0x38+i*4).readU32())};
 }
 if(appearances.length){
  b.add(0xAC63C).writeU8(3);
  const obj=Memory.alloc(0x2040),dispatch=new NativeFunction(b.add(0x109EF),'uint',['pointer'],'fastcall');
  function states(){const rows=[];for(let i=0;i<115;i++){const p=b.add(0xB2C50+i*36);if(p.readU32()!==65535)rows.push({slot:i,id:p.readU32(),type:p.add(12).readU8(),position:[p.add(6).readU8(),p.add(7).readU8()]});}return rows;}
  for(const event of appearances){
   const before=states(),input=buffer(event.bytes);obj.writeByteArray(new Uint8Array(0x2040));obj.add(12).writePointer(input);
   const status=dispatch(obj)&255;
   const after=states();appearanceResults.push({offset:event.offset,status,consumed:obj.add(12).readPointer().sub(input).toInt32(),changes:after.filter((p,i)=>JSON.stringify(p)!==JSON.stringify(before[i]))});
  }
 }
 const hp=new NativeFunction(b.add(0x0721B),'uint',['pointer','uint'],'fastcall');
 const mp=new NativeFunction(b.add(0x0724A),'uint',['pointer','uint'],'fastcall');
 const art=new NativeFunction(b.add(0x3FC48),'uint',['pointer'],'fastcall');
 const attack=new NativeFunction(b.add(0x3F4FE),'uint',['pointer'],'fastcall');
 const defense=new NativeFunction(b.add(0x3F595),'uint',['pointer'],'fastcall');
 const agility=new NativeFunction(b.add(0x3F631),'uint',['pointer'],'fastcall');
 const luck=new NativeFunction(b.add(0x3F67F),'uint',['pointer'],'fastcall');
 const movement=new NativeFunction(b.add(0x3F74F),'uint8',['pointer'],'fastcall');
 const units=[];
 for(let i=0;i<115;i++){
  const slot=b.add(0xB2C50+i*36);if(slot.readU32()===65535)continue;
  const id=slot.readU32(),unit=b.add(0xA1B68+id*72);
  units.push({slot:i,unitId:id,slotNumber:slot.add(4).readU8(),variant:slot.add(5).readU8(),
   type:slot.add(12).readU8(),position:[slot.add(6).readU8(),slot.add(7).readU8()],actorFlags:slot.add(13).readU8(),facing:slot.add(15).readU8(),classId:unit.add(43).readU8(),
   level:unit.add(44).readU8(),hp:slot.add(16).readU32(),mp:slot.add(20).readU32(),
   maxHp:hp(unit,0),maxMp:mp(unit,0),art:art(slot)&255,
   combat:{attack:attack(slot),defense:defense(slot),agility:agility(slot),luck:luck(slot)},
   nativeMove:movement(slot),
   equipment:Array.from({length:3},(_,s)=>Array.from(new Uint8Array(unit.add(46+s*3).readByteArray(3)))),
   actorHex:Array.from(new Uint8Array(slot.readByteArray(36))).map(x=>x.toString(16).padStart(2,'0')).join(''),
   unitHex:Array.from(new Uint8Array(unit.readByteArray(72))).map(x=>x.toString(16).padStart(2,'0')).join('')});
 }
 const occupancy=placement?Array.from(new Uint8Array(b.add(0xAEB38+12).readPointer().add(0xC80).readByteArray(mapSize[0]*mapSize[1]))):null;
 return {units,moves,appearanceResults,eventExecution,occupancy};
}};
''');script.load()
        terrain=dict(entries(ROOT/'Hexzmap.e5'))[0][2:]
        result=script.exports_sync.capture({str(k):list(data[k]) for k in (0,1,3,4)},snapshot,args.placement,list(terrain),appearance_cases,event_file,args.liu_movement or args.victory_movement,args.victory_event,args.fallen_ally)
        result['scope']='real native DATA character/item/class loaders and0x44CC85, level/equipment/stat rules; coordinate entry0x442B03, UI refresh, AI script binding and file-load leaves intercepted; initial campaign progress not supplied'
        if args.placement and not args.appearances and not args.liu_event and not args.victory_event:
            result['scope']='native DATA loaders,0x44CC85 and0x442B03 coordinate entry with map0 terrain/occupancy; mirror pixels replaced while preserving native flag setters; UI/AI binding and file load intercepted; no campaign initialization/post-entry script'
            scene=json.loads((ROOT/'analysis/s00-units-readable.json').read_text(encoding='utf-8'))
            lookup={u['unitId16']:u for u in scene['units']}
            checks=[]
            occupied=set()
            for unit in result['units']:
                source=lookup[unit['unitId']]
                hidden=bool(source['flagsU32']&4)
                expected_position=[255,255] if hidden else source['coordinateBytes']
                position=tuple(unit['position'])
                checks.append(dict(unitId=unit['unitId'],hidden=hidden,
                                   match=unit['type']==(1 if hidden else 2) and unit['position']==expected_position,
                                   expected_position=expected_position))
                if not hidden:
                    if position in occupied:raise ValueError('Overlapping placed units')
                    occupied.add(position)
            result['placement_checks']=checks
            result['placement_checks_passed']=all(c['match'] for c in checks)
            result['placed_count']=len(occupied)
            if not result['placement_checks_passed']:raise ValueError('Placement differs from scene flags/coordinates')
        filename='native-s00-placed-units.json' if args.placement else 'native-s00-expanded-units.json'
        if args.appearances:
            filename='native-s00-appearance-transitions.json'
            result['script_conditions']=appearance_cases
            result['scope']='opcode76 dispatch and native appearance/coordinate transitions after controlled DATA initialization; presentation/sound/wait callbacks intercepted; predicates recorded but not evaluated; intervening story actions omitted'
            sources=json.loads((ROOT/'analysis/s00-units-readable.json').read_text(encoding='utf-8'))['units']
            lookup={u['unitId16']:u for u in sources}
            checks=[]
            for case,row in zip(appearance_cases,result['appearanceResults']):
                node=next(n for branch in json.loads((ROOT/'analysis/eex-bodies/S_00.json').read_text(encoding='utf-8'))
                          for n,_ in walk(branch['nodes']) if n['offset']==case['offset'])
                identity=node['arguments'][1]['value'] if node['arguments'][0]['value']==0 else 0
                source=lookup[identity]
                wanted=[dict(slot=source['nativeBattleSlot'],id=identity,type=2,position=source['coordinateBytes'])]
                checks.append(dict(offset=case['offset'],expected=wanted,match=row['status']==1
                                   and row['consumed']==len(case['bytes']) and row['changes']==wanted))
            result['appearance_checks']=checks
            result['appearance_checks_passed']=len(checks)==7 and all(c['match'] for c in checks)
            if not result['appearance_checks_passed']:raise ValueError('Appearance transition mismatch')
        if args.liu_event:
            filename='native-s00-liu-event-validation.json'
            event=result['eventExecution']
            expected_moves=[dict(kind='move-request',actor=actor,x=x,y=5,direction=2) for actor,x in ((32,11),(3,10),(33,12))]
            calls=event['calls']
            result['passed']=(event['selected']==1 and event['result']==4 and event['flag11']==1 and event['selectedAgain']==0
                              and [c['speaker'] for c in calls if c['kind']=='dialogue']==[32,3,33,32]
                              and (args.liu_movement or ([c for c in calls if c['kind']=='move-request']==expected_moves
                              and [c['kind'] for c in calls]==['dialogue','orient','orient','dialogue','dialogue','dialogue','move-request','move-request','move-request'])))
            result['scope']='byte-exact original S_00 branch1/1 predicates/body in minimal EEX; real selection/interpreter/dialogue parsing/appearance/flag11; orient and move leaves captured without applying movement; no real UI/audio or full18-branch scheduling'
            if not result['passed']:raise ValueError(f'Event mismatch: {event}')
            if args.liu_movement:
                filename='native-s00-liu-movement-validation.json'
                paths=[c for c in calls if c['kind']=='native-path']
                result['scope']='original event interpreter and0x459487 wrapper; real0x438308 search/0x43A956 coordinate stepping;0x43AD1C AI prepass replaced by controlled search call; per-cell drawing/audio/UI suppressed; not full native AI movement workflow'
                result['passed']=result['passed'] and len(paths)==3 and all(p['search']==1 and p['position']==p['target'] for p in paths)
                checks=[]
                vectors=[(0,-1),(1,0),(0,1),(-1,0)]
                by_id={u['unitId']:u for u in result['units']}
                for path in paths:
                    continuous=True
                    for i,step in enumerate(path['steps']):
                        dx,dy=vectors[step['direction']]
                        next_position=[step['from'][0]+dx,step['from'][1]+dy]
                        expected_next=path['steps'][i+1]['from'] if i+1<len(path['steps']) else path['position']
                        continuous=continuous and next_position==expected_next
                    unit=by_id[path['actor']];x,y=unit['position']
                    checks.append(dict(actor=path['actor'],steps=len(path['steps']),continuous=continuous,
                                       facing=unit['facing'],occupiedBy=result['occupancy'][x+y*20],
                                       match=continuous and unit['facing']==2 and result['occupancy'][x+y*20]==unit['slot']))
                result['path_checks']=checks
                result['passed']=result['passed'] and all(c['match'] for c in checks)
                if not result['passed']:raise ValueError(f'Movement mismatch: {paths}')
        if args.victory_event:
            filename='native-s00-full-victory-event.json'
            event=result['eventExecution']
            enemies=[u for u in result['units'] if u['slot']>=35]
            result['scope']='byte-exact full original branch9 with actual native area removal, healing, dialogue parsing, treasury and flags; all18 scheduling not used; flags50/51 supplied and hidden allies activated as fixture; move/orient requests captured without application; display/audio suppressed; no complete battle/campaign'
            result['passed']=(event['selected']==1 and event['result']==4 and event['selectedAgain']==0
                              and event['money']==800 and event['battleState']==2 and event['completionFlags']==[1,1,1]
                              and len(enemies)==14 and all(u['type']==3 for u in enemies))
            if not result['passed']:raise ValueError(f'Victory event mismatch: {event}')
            if args.victory_movement:
                filename='native-s00-victory-movement-validation.json'
                paths=[c for c in event['calls'] if c['kind']=='native-path']
                expected=[(210,[8,15]),(211,[8,16]),(234,[8,17]),(258,[8,18]),(259,[8,19]),(0,[10,19])]
                checks=[]
                vectors=[(0,-1),(1,0),(0,1),(-1,0)]
                by_id={u['unitId']:u for u in result['units']}
                for path,(actor,target) in zip(paths,expected):
                    continuous=True
                    for i,step in enumerate(path['steps']):
                        dx,dy=vectors[step['direction']]
                        following=path['steps'][i+1]['from'] if i+1<len(path['steps']) else path['position']
                        continuous=continuous and [step['from'][0]+dx,step['from'][1]+dy]==following
                    unit=by_id[actor];x,y=unit['position']
                    checks.append(dict(actor=actor,steps=len(path['steps']),continuous=continuous,
                                       match=path['actor']==actor and path['target']==target and path['search']==1
                                       and path['position']==target and unit['position']==target and continuous
                                       and unit['facing']==2 and result['occupancy'][x+y*20]==unit['slot']))
                result['path_checks']=checks
                result['passed']=result['passed'] and len(paths)==6 and all(c['match'] for c in checks)
                result['scope']='original branch9 interpreter, removal/dialogue/reward/flags plus real0x459487,0x438308,0x437E2E,0x43A956 paths; AI prepass replaced by controlled native search, pixel/audio/UI/orient suppressed; supplied death flags/active allies fixture, not battle playthrough'
                if not result['passed']:raise ValueError(f'Victory paths mismatch: {checks}')
            if args.fallen_ally is not None:
                filename=f'native-s00-victory-fallen-{args.fallen_ally}.json'
                calls=event['calls']
                result['fallen_fixture']=dict(actor=args.fallen_ally,flag={32:52,3:53,33:54}[args.fallen_ally])
                result['scope']='original full branch9, DATA initialized, supplied death flags and native ally removal fixture; real conditional fallback/dialogue parsing/treasury/end flags; presentation suppressed, no actual battle or death-flag generation'
                result['passed']=result['passed'] and [c['speaker'] for c in calls if c['kind']=='dialogue']==[0,0]
                result['passed']=result['passed'] and not any(c['kind'] in ('orient','move-request','native-path') for c in calls)
                result['passed']=result['passed'] and next(u for u in result['units'] if u['unitId']==args.fallen_ally)['type']==3
                if not result['passed']:raise ValueError(f'Fallback victory mismatch: {event}')
        (ROOT/'analysis'/filename).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print('S_00 expanded units:',len(result['units']))
        if 'passed' in result:print(f'{filename}: passed={result["passed"]}')
        print([(u['unitId'],u['classId'],u['level'],u['hp'],u['maxHp'],u['art']) for u in result['units']])
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
