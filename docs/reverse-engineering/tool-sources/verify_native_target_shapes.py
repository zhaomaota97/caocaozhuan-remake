"""Cross-check native attack/effect range geometry, including clipping at map edges."""
import ast
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]
tree=ast.parse((ROOT/'tools/export_slot08_native_health.py').read_text(encoding='utf-8'))
sources=[node.args[0].value for node in ast.walk(tree)
         if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
         and node.func.attr=='create_script' and isinstance(node.args[0],ast.Constant)]
if len(sources)!=1 or sources[0].count('return out;')!=1:
    raise RuntimeError('Review native initialization before reuse')
source=sources[0].replace('return out;', '''
 const generate=new NativeFunction(b.add(0x36586),'uint8',
  ['pointer','pointer','uint','uint8','uint8'],'thiscall');
 const secondary=b.add(0xaab68).add(12).readPointer(),rows=[];
 for(const origin of [[8,8],[0,0],[19,0],[0,31],[19,31]])
 for(let shape=0;shape<16;shape++)for(const high of [0,128])for(const flags of [0,1]){
  battlefield.add(0x12c0).writeByteArray(new Uint8Array(640).fill(255));
  secondary.add(0xc80).writeByteArray(new Uint8Array(640));
  coordinate.writeU8(origin[0]);coordinate.add(1).writeU8(origin[1]);
  const returned=generate(b.add(0xb2c50),coordinate,shape|high,flags,1);
  const cells=[],costs=[];
  for(let i=0;i<640;i++){
   if(secondary.add(0xc80+i).readU8())cells.push(i);
   if(battlefield.add(0x12c0+i).readU8()!==255)costs.push(i);
  }
  rows.push({origin,shape,high,flags,returned,cells,costs});
 }
 return {diagonals:Array.from({length:4},(_,i)=>[b.add(0x8df48+i*8).readS32(),b.add(0x8df4c+i*8).readS32()]),rows};
''')

def offsets(shape, diagonals):
    cross={(0,-1),(1,0),(0,1),(-1,0)}
    diagonal=set(map(tuple,diagonals))
    axes=lambda radius:{(0,-radius),(radius,0),(0,radius),(-radius,0)}
    stripes=lambda radius,half:{point for value in range(-half,half+1)
                               for point in ((value,-radius),(value,radius),(-radius,value),(radius,value))}
    third=diagonal|stripes(2,1)|axes(3)
    fourth=diagonal|stripes(2,1)|stripes(3,1)|{(-2,-2),(-2,2),(2,-2),(2,2)}|axes(4)
    ring=lambda radius:{(x,y) for x in range(-radius,radius+1) for y in range(-radius,radius+1)
                        if abs(x)+abs(y)==radius}
    return {0:cross,1:cross|diagonal,2:diagonal|axes(2),3:third,4:fourth,
            5:cross|axes(2),6:cross|diagonal|axes(2),7:ring(4),8:ring(4)|ring(5),
            9:axes(2),11:set(),12:cross|third,13:cross|fourth,
            14:stripes(3,1),15:stripes(3,2)}.get(shape,set())

data=dict(entries(ROOT/'Data.e5'))
device=frida.get_local_device()
pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'))
session=None
try:
    session=device.attach(pid)
    script=session.create_script(source);script.load()
    result=script.exports_sync.read(list(data[0]),list(data[1]),list(data[3]),list(data[4]),
        list((ROOT/'Sv08d.e5s').read_bytes()[0x14dc:]),
        list((ROOT/'Sv08s.e5s').read_bytes()[1301:4291]),
        list((ROOT/'analysis/saved-battlefields/Sv08s-terrain.bin').read_bytes()))
    for row in result['rows']:
        x,y=row['origin']
        cells=offsets(row['shape'],result['diagonals'])
        if row['flags']&1:
            cells=cells|{(0,0)}
        expected=(list(range(640)) if row['shape']==10 else
                  sorted((y+dy)*20+x+dx for dx,dy in cells if 0<=x+dx<20 and 0<=y+dy<32))
        row['match']=row['cells']==expected and row['costs']==expected and row['returned']==255
    result.update(function='0x436586',mode=1,total=len(result['rows']),
                  matched=sum(row['match'] for row in result['rows']))
    (ROOT/'analysis/native-target-shapes.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f"Native target shapes: {result['matched']}/{result['total']}")
    if result['matched']!=result['total']:
        raise SystemExit('Range geometry mismatch')
    geometry=[{'id':shape,'fullMap':shape==10,'hasExplicitBranch':shape!=11,
               'offsets':[list(point) for point in sorted(offsets(shape,result['diagonals']))]}
              for shape in range(16)]
    (ROOT.parent/'caocaozhuan-remake/data/rules/target-shapes.json').write_text(json.dumps({
        'function':'0x436586','shapeMask':127,'includeOriginFlag':1,'shapes':geometry},indent=2)+'\n',encoding='utf-8')
finally:
    device.kill(pid)
    if session:
        session.detach()
