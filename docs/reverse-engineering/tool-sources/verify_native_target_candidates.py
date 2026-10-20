"""Capture original target-list order, faction/HP filtering, and preferred-target return."""
import ast
import json
import os
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]
case_actor_limit=max(1,int(os.environ.get('TARGET_ACTOR_LIMIT','32')))
case_actor_offset=max(0,int(os.environ.get('TARGET_ACTOR_OFFSET','0')))
case_shape_limit=max(1,min(16,int(os.environ.get('TARGET_SHAPE_LIMIT','16'))))
case_shape_offset=max(0,min(15,int(os.environ.get('TARGET_SHAPE_OFFSET','0'))))
health_modes=[mode for mode in os.environ.get('TARGET_HEALTH_MODES','saved,alternate-zero').split(',') if mode in {'saved','alternate-zero'}]
if not health_modes:
    health_modes=['saved']
flag_values=[int(value) for value in os.environ.get('TARGET_FLAGS','0,1').split(',') if value in {'0','1'}]
if not flag_values:
    flag_values=[0]
tree=ast.parse((ROOT/'tools/export_slot08_native_health.py').read_text(encoding='utf-8'))
sources=[node.args[0].value for node in ast.walk(tree)
         if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
         and node.func.attr=='create_script' and isinstance(node.args[0],ast.Constant)]
if len(sources)!=1 or sources[0].count('return out;')!=1:
    raise RuntimeError('Review native initialization before reuse')
source=sources[0].replace('return out;', '''
 const generate=new NativeFunction(b.add(0x36586),'uint8',
  ['pointer','pointer','uint','uint8','uint8'],'thiscall');
 Process.setExceptionHandler(e=>{send({exception:e.type,pc:e.context.pc.toString()});return false;});
 Interceptor.attach(Module.getGlobalExportByName('ExitProcess'),{onEnter(args){send({exitCode:args[0].toUInt32()});}});
 function candidates(){
  const list=[];
  for(let i=0;i<116;i++){
   const id=b.add(0xac748+i).readU8();if(id===255)return list;list.push(id);
  }
  throw new Error('Unterminated native target list');
 }
 const occupancy=Array.from(new Uint8Array(battlefield.add(0xc80).readByteArray(640))),rows=[],cases=[];
 for(const healthMode of ${json.dumps(health_modes)}){
  for(const row of out)b.add(0xb2c50+row.slot*36+16).writeU32(healthMode==='alternate-zero' && row.slot%2===0 ? 0 : row.hp);
  for(const actorRow of out.slice(${case_actor_offset},${case_actor_offset}+${case_actor_limit}))for(let shape=${case_shape_offset};shape<${case_shape_offset}+${case_shape_limit}&&shape<16;shape++)for(const flags of ${json.dumps(flag_values)}){
   if(actorRow.slot===0)send({healthMode,shape,flags});
   const a=b.add(0xb2c50+actorRow.slot*36);
   // Native AI callers clear the target/effect view before 0x436586. The
   // movement probe initializes occupancy but not this adjacent 0x640-byte
   // view, which can leave stale pointers when probing later actor slots.
   battlefield.add(0x12c0).writeByteArray(new Uint8Array(0x640).fill(255));
   b.add(0xb2c28).writeU8(255);generate(a,a.add(6),shape,flags,0);
   const list=candidates(),caseIndex=cases.length;
   cases.push({slot:actorRow.slot,shape,flags,healthMode,origin:[a.add(6).readU8(),a.add(7).readU8()]});
   const preferredValues=Array.from(new Set([255,114,...(list.length ? [list[0],list[list.length-1]] : [])]));
   for(const preferred of preferredValues){
    b.add(0xb2c28).writeU8(preferred);
    const returned=generate(a,a.add(6),shape,flags,0);
    rows.push({caseIndex,preferred,returned,candidates:candidates()});
   }
  }
 }
 return {diagonals:Array.from({length:4},(_,i)=>[b.add(0x8df48+i*8).readS32(),b.add(0x8df4c+i*8).readS32()]),
  actors:out.map(row=>({slot:row.slot,hp:row.hp})),occupancy,cases,rows};
''')
source=source.replace('${case_actor_offset}',str(case_actor_offset)).replace('${case_actor_limit}',str(case_actor_limit)).replace('${case_shape_offset}',str(case_shape_offset)).replace('${case_shape_limit}',str(case_shape_limit))
source=source.replace('${json.dumps(health_modes)}',json.dumps(health_modes)).replace('${json.dumps(flag_values)}',json.dumps(flag_values))

def ordered_offsets(shape,diagonal):
    cross=[(0,-1),(1,0),(0,1),(-1,0)]
    diagonal=list(map(tuple,diagonal))
    axes=lambda r:[(-r,0),(r,0),(0,-r),(0,r)]
    stripes=lambda r:[p for v in range(-1,2) for p in ((v,-r),(v,r))]+[p for v in range(-1,2) for p in ((r,v),(-r,v))]
    third=diagonal+stripes(2)+axes(3)
    fourth=diagonal+stripes(2)+stripes(3)+[(-2,-2),(2,2),(2,-2),(-2,2)]+axes(4)
    ring=lambda r:[(x,y) for y in range(-r,r+1) for x in range(-r,r+1) if abs(x)+abs(y)==r]
    return {0:cross,1:cross+diagonal,2:diagonal+axes(2),3:third,4:fourth,5:cross+axes(2),
            6:cross+diagonal+axes(2),7:ring(4),8:ring(4)+ring(5),9:axes(2),11:[],
            12:cross+third,13:cross+fourth,
            14:[p for v in range(-1,2) for p in ((-3,v),(3,v),(v,-3),(v,3))],
            15:[p for v in range(-2,3) for p in ((v,-3),(v,3),(-3,v),(3,v))]}.get(shape,[])
data=dict(entries(ROOT/'Data.e5'))
device=frida.get_local_device()
pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'))
session=None
try:
    session=device.attach(pid)
    script=session.create_script(source)
    script.on('message',lambda message,data: print(message))
    script.load()
    try:
        result=script.exports_sync.read(list(data[0]),list(data[1]),list(data[3]),list(data[4]),
            list((ROOT/'Sv08d.e5s').read_bytes()[0x14dc:]),
            list((ROOT/'Sv08s.e5s').read_bytes()[1301:4291]),
            list((ROOT/'analysis/saved-battlefields/Sv08s-terrain.bin').read_bytes()))
    except (frida.InvalidOperationError, frida.ProcessNotFoundError) as exc:
        boundary={'actorOffset':case_actor_offset,'actorLimit':case_actor_limit,
                  'shapeOffset':case_shape_offset,'shapeLimit':case_shape_limit,
                  'healthModes':health_modes,'flags':flag_values,
                  'status':'script-destroyed','error':repr(exc)}
        out_name=ROOT/'analysis'/f'target-shape-boundary-{case_actor_offset}-{case_shape_offset}.json'
        out_name.write_text(json.dumps(boundary,indent=2)+'\n',encoding='utf-8')
        print(f'Target candidate boundary: {out_name.name}')
        raise SystemExit(2)
    health={row['slot']:row['hp'] for row in result['actors']}
    for row in result['rows']:
        case=result['cases'][row['caseIndex']]
        expected=[]
        x,y=case['origin']
        points=([(0,0)] if case['flags']&1 else [])+ordered_offsets(case['shape'],result['diagonals'])
        visits=([dy*20+dx for dy in range(32) for dx in range(20)] if case['shape']==10 else
                [(y+dy)*20+x+dx for dx,dy in points if 0<=x+dx<20 and 0<=y+dy<32])
        if case['shape']==10 and case['flags']&1:
            visits=[y*20+x]+visits
        for index in visits:
            occupant=result['occupancy'][index]
            if occupant==255 or not health[occupant]:
                continue
            if case['healthMode']=='alternate-zero' and occupant%2==0:
                continue
            friendly=(case['slot']<35)==(occupant<35)
            if friendly==bool(case['flags']&1):
                expected.append(occupant)
        returned=row['preferred'] if row['preferred'] in expected else expected[-1] if expected else 255
        row['match']=row['candidates']==expected and row['returned']==returned
    result.update(function='0x436586',mode=0,total=len(result['rows']),
                  matched=sum(row['match'] for row in result['rows']))
    output_name='native-target-candidates.json' if (case_actor_offset==0 and case_actor_limit>=32 and case_shape_offset==0 and case_shape_limit>=16) else f'native-target-candidates-limit-{case_actor_offset}-{case_actor_limit}x{case_shape_offset}-{case_shape_limit}.json'
    (ROOT/'analysis'/output_name).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f"Native target candidates: {result['matched']}/{result['total']}")
    if result['matched']!=result['total']:
        raise SystemExit('Target candidate mismatch')
finally:
    device.kill(pid)
    if session:
        session.detach()
