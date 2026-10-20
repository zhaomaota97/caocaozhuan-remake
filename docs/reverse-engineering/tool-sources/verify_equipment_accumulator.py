"""Execute full native equipment attribute accumulator on real item definitions."""
import ast
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]
tree = ast.parse((ROOT / 'tools/export_slot08_native_health.py').read_text(encoding='utf-8'))
sources = [node.args[0].value for node in ast.walk(tree) if isinstance(node, ast.Call)
           and isinstance(node.func, ast.Attribute) and node.func.attr == 'create_script'
           and isinstance(node.args[0], ast.Constant)]
assert len(sources) == 1 and sources[0].count('return out;') == 1
source = sources[0].replace('return out;', r'''
 const sum=new NativeFunction(b.add(0x7c0e),'uint',['pointer','uint','uint'],'fastcall');
 const u=b.add(0xa1b68),definitions=[],rows=[];
 for(let id=0;id<104;id++){
  const p=b.add(0xa1140+id*25);
  definitions.push({id,categoryByte:p.add(17).readU8(),equipmentEffectCategory:p.add(20).readU8(),baseValue:p.add(21).readU8(),secondaryValue:p.add(22).readU8(),growthValue:p.add(23).readU8()});
 }
 function capture(ids,level){
  for(let s=0;s<3;s++){u.add(46+s*3).writeU8(ids[s]);u.add(47+s*3).writeU8(level);}
  rows.push({ids,level,values:Array.from({length:9},(_,category)=>sum(u,0,category)&255)});
 }
 for(let id=0;id<104;id++)for(const level of [0,1,3,9,255]){
  for(let slot=0;slot<3;slot++){const ids=[255,255,255];ids[slot]=id;capture(ids,level);}
  capture([id,id,id],level);
  capture([id,(id+37)%104,(id+71)%104],level);
 }
 return {definitions,rows};
''')

def primary(category):
    if category < 10 or category == 24: return 0
    if category < 14 or category == 25: return 2
    if category < 18 or category == 26: return 1
    return {27:3,28:4,29:5,30:6,32:7,31:8}.get(category,255)

def expected(definitions, ids, level, category):
    total = 0
    for slot, item_id in enumerate(ids):
        if item_id == 255: continue
        item = definitions[item_id]
        kind = item['categoryByte']
        if primary(kind) == category:
            value = min(255,item['baseValue']+max(0,level-1)*item['growthValue']) if slot < 2 and kind < 18 else item['baseValue']
            total += value
        if slot < 2 and kind < 18 and kind & 1 and {24:0,25:2,26:1,27:3,28:4,29:5,30:6,31:8,32:7}.get(item['equipmentEffectCategory'],255) == category:
            total += item['secondaryValue']
    return total & 255

device = frida.get_local_device()
pid = device.spawn([str(ROOT / 'analysis/runtime-game/Ekd5.exe')], cwd=str(ROOT / 'analysis/runtime-game'))
session = None
try:
    session=device.attach(pid)
    script=session.create_script(source)
    script.load()
    data=dict(entries(ROOT/'Data.e5'))
    result=script.exports_sync.read(list(data[0]),list(data[1]),list(data[3]),list(data[4]),list((ROOT/'Sv08d.e5s').read_bytes()[0x14dc:]),list((ROOT/'Sv08s.e5s').read_bytes()[1301:4291]),list((ROOT/'analysis/saved-battlefields/Sv08s-terrain.bin').read_bytes()))
    failures=[]
    for row in result['rows']:
        calculated=[expected(result['definitions'],row['ids'],row['level'],category) for category in range(9)]
        if calculated != row['values']: failures.append(dict(row,expected=calculated))
    result.update(passed=not failures,address='0x407C0E',comparisons=len(result['rows'])*9)
    text=json.dumps(result,indent=2)+'\n'
    (ROOT/'analysis/native-equipment-accumulator.json').write_text(text,encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-equipment-accumulator.json').write_text(text,encoding='utf-8')
    print(f'Native equipment accumulator: {len(result["rows"])-len(failures)}/{len(result["rows"])} loadouts; {result["comparisons"]} category comparisons')
    if failures: raise RuntimeError(failures[0])
finally:
    device.kill(pid)
    if session: session.detach()
