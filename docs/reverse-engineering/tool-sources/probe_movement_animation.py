"""Execute native per-cell animation; capture draws while replacing presentation sinks."""
import ast
import json
import sys
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]
tree = ast.parse((ROOT/'tools/export_slot08_native_health.py').read_text(encoding='utf-8'))
sources = [node.args[0].value for node in ast.walk(tree)
           if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
           and node.func.attr=='create_script' and isinstance(node.args[0],ast.Constant)]
if len(sources)!=1 or sources[0].count('return out;')!=1:
    raise RuntimeError('Review native initialization before reuse')
source = sources[0].replace('return out;', '''
 const callbacks=[];let draws=[],ticks=[],waits=0,mirrors=[];
 function replace(rva,args,abi,fn){
  const callback=new NativeCallback(fn || (()=>{}),'void',args,abi);
  callbacks.push(callback);Interceptor.replace(b.add(rva),callback);
 }
 replace(0x7e251,['int','int','uint','int','pointer'],'mscdecl');
 replace(0x51913,['int','int','uint','int','pointer','uint'],'mscdecl');
 replace(0x36f9,['int','int'],'mscdecl');
 replace(0x3eb1f,['int','int','int'],'mscdecl');
 replace(0x1e5db,[],'mscdecl');replace(0x1e5f6,[],'mscdecl');
 replace(0x3340,['pointer','int'],'thiscall',(self,tick)=>{ticks.push(tick);});
 replace(0x2c4e0,[],'mscdecl',()=>{waits++;});
 replace(0x3fd34,['pointer','int'],'thiscall',(self,mirror)=>{mirrors.push(mirror);});
 replace(0x7467a,['pointer','int','int'],'thiscall');
 const frameBase=Memory.alloc(115*0x6300);
 const frameView=b.add(0xaab80);
 frameView.add(4).writeU32(115*0x6300);frameView.add(12).writePointer(frameBase);frameView.add(16).writeU8(1);
 view(0xae4c8);
 const camera=b.add(0xb4250);
 camera.add(4).writeU32(0);camera.add(8).writeU32(0);
 camera.add(0x14).writeU32(20*48);camera.add(0x18).writeU32(32*48);
 replace(0x5137c,['int','int','uint','uint','uint','pointer'],'mscdecl',
  (x,y,w,h,slot,frame)=>{draws.push({x,y,w,h,slot,frameOffset:frame.sub(frameBase).toInt32()});});
 Interceptor.flush();
 const animate=new NativeFunction(b.add(0x4201b),'void',['pointer','uint8'],'thiscall');
 const a=b.add(0xb2c50),u=b.add(0xa1b68),rows=[];
 a.add(6).writeU8(8);a.add(7).writeU8(8);
 for(let classId=0;classId<53;classId++)for(let setting=0;setting<3;setting++)for(let direction=0;direction<4;direction++){
  u.add(0x2b).writeU8(classId);b.add(0xb0778).writeU8(setting);
  draws=[];ticks=[];waits=0;mirrors=[];animate(a,direction);
  rows.push({classId,setting,direction,draws,ticks,waits,mirrors,
   directionAfter:a.add(15).readU8(),positionAfter:[a.add(6).readU8(),a.add(7).readU8()]});
 }
 return rows;
''')
camera_mode = '--camera' in sys.argv
if camera_mode:
    source = source.replace('let draws=[],ticks=[],waits=0,mirrors=[];',
                            'let draws=[],ticks=[],waits=0,mirrors=[],scrolls=[];')
    source = source.replace('Interceptor.flush();\n const animate=', '''
 replace(0x54b7e,['pointer','uint','uint','uint8'],'thiscall',
  (self,x,y,mode)=>{scrolls.push({x,y,mode});});
 Interceptor.flush();
 const animate=''', 1)
    source = source.replace('for(let classId=0;', '''
 const scenarios=[
  {name:'interior',cx:0,cy:0,w:20,h:32,x:8,y:8},
  {name:'north-edge',cx:2,cy:2,w:4,h:4,x:3,y:2},
  {name:'east-edge',cx:2,cy:2,w:4,h:4,x:5,y:3},
  {name:'south-edge',cx:2,cy:2,w:4,h:4,x:3,y:5},
  {name:'west-edge',cx:2,cy:2,w:4,h:4,x:2,y:3},
  {name:'map-lower-right',cx:16,cy:28,w:4,h:4,x:18,y:30}];
 for(const scenario of scenarios){
 camera.add(4).writeU32(scenario.cx*48);camera.add(8).writeU32(scenario.cy*48);
 camera.add(0x14).writeU32(scenario.w*48);camera.add(0x18).writeU32(scenario.h*48);
 a.add(6).writeU8(scenario.x);a.add(7).writeU8(scenario.y);
 for(let classId=0;''', 1)
    source = source.replace('draws=[];ticks=[];waits=0;mirrors=[];',
                            'draws=[];ticks=[];waits=0;mirrors=[];scrolls=[];')
    source = source.replace('rows.push({classId,', 'rows.push({scenario,scrolls,classId,')
    source = source.replace('return rows;', '}\n return rows;')
data = dict(entries(ROOT/'Data.e5'))
device = frida.get_local_device()
pid = device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'))
session = None
try:
    session = device.attach(pid)
    script = session.create_script(source)
    script.load()
    rows = script.exports_sync.read(list(data[0]),list(data[1]),list(data[3]),list(data[4]),
        list((ROOT/'Sv08d.e5s').read_bytes()[0x14dc:]),
        list((ROOT/'Sv08s.e5s').read_bytes()[1301:4291]),
        list((ROOT/'analysis/saved-battlefields/Sv08s-terrain.bin').read_bytes()))
    for row in rows:
        kind = row['classId']//3 if row['classId']<39 else row['classId']-26
        step = ([48,24,12] if kind in (0,3,4,11,13,17,20) else [48,12,6])[row['setting']]
        direction = row['direction']
        dx,dy = [(0,-1),(1,0),(0,1),(-1,0)][direction]
        bank = [1,2,0,2][direction]
        scenario = row.get('scenario',dict(cx=0,cy=0,w=20,h=32,x=8,y=8))
        cx,cy,x,y = [scenario[key] for key in ('cx','cy','x','y')]
        scroll = (direction==0 and cy!=0 and cy>=y-1
                  or direction==1 and x+1>=cx+scenario['w'] and cx+scenario['w']<20
                  or direction==2 and y+1>=cy+scenario['h'] and cy+scenario['h']<32
                  or direction==3 and cx!=0 and cx>=x-1)
        start_x,start_y = x-cx,y-cy
        if scroll:
            start_x-=dx
            start_y-=dy
        expected = [{'x':start_x*48+dx*progress,'y':start_y*48+56+dy*progress,
                     'w':48,'h':48,'slot':0,
                     'frameOffset':bank*0x1200+((progress-1)//24)*0x900}
                    for progress in range(step,49,step)]
        row['match'] = (row['draws']==expected and row['ticks']==[1]*len(expected)
            and row['waits']==len(expected) and row['directionAfter']==direction
            and row['positionAfter']==[x,y]
            and row['mirrors']==([1] if direction==1 else [0] if direction==3 else []))
        if camera_mode:
            row['match'] = row['match'] and row['scrolls']==([dict(x=cx+dx,y=cy+dy,mode=0)] if scroll else [])
    result = {'function':'0x44201B','scope':'graphics/timers/audio sinks replaced; scroll requests captured' if camera_mode else 'interior camera position, graphics/timers/audio sinks replaced',
              'total':len(rows),'matched':sum(row['match'] for row in rows),'rows':rows}
    name = 'native-movement-camera.json' if camera_mode else 'native-movement-animation.json'
    (ROOT/'analysis'/name).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f"Native movement animation draws: {result['matched']}/{result['total']}")
    if result['matched']!=result['total']:
        raise SystemExit('Animation probe mismatch; inspect output')
finally:
    device.kill(pid)
    if session:
        session.detach()
