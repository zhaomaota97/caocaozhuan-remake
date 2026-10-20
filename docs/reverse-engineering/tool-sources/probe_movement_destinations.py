"""Probe original player destination acceptance, separately from reachability."""
import ast
import json
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
 const accepts=new NativeFunction(b.add(0x401a8),'uint',['pointer','pointer'],'thiscall');
 const rows=[],synthetic=[];
 for(const row of out){
  const a=b.add(0xb2c50+row.slot*36);
  rows.push({slot:row.slot,accepted:Array.from({length:640},(_,index)=>{
   coordinate.writeU8(index%20);coordinate.add(1).writeU8(Math.floor(index/20));
   return accepts(a,coordinate)!==0;
  })});
 }
 const occupant=b.add(0xb2c50+114*36),previous=occupant.add(12).readU8();
 coordinate.writeU8(0);coordinate.add(1).writeU8(0);battlefield.add(0xc80).writeU8(114);
 for(const row of out)for(let state=0;state<5;state++)for(let terrain=0;terrain<30;terrain++){
  occupant.add(12).writeU8(state);battlefield.add(0x640).writeU8(terrain);
  synthetic.push({slot:row.slot,state,terrain,accepted:accepts(b.add(0xb2c50+row.slot*36),coordinate)!==0});
 }
 occupant.add(12).writeU8(previous);
 return {rows,synthetic};
''')
data = dict(entries(ROOT/'Data.e5'))
device = frida.get_local_device()
pid = device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'))
session = None
try:
    session = device.attach(pid)
    script = session.create_script(source)
    script.load()
    fixture = script.exports_sync.read(list(data[0]),list(data[1]),list(data[3]),list(data[4]),
        list((ROOT/'Sv08d.e5s').read_bytes()[0x14dc:]),
        list((ROOT/'Sv08s.e5s').read_bytes()[1301:4291]),
        list((ROOT/'analysis/saved-battlefields/Sv08s-terrain.bin').read_bytes()))
    actors = json.loads((ROOT/'analysis/slot08-native-health.json').read_text(encoding='utf-8'))
    costs = {row['slot']:row['terrainCosts'] for row in actors}
    save = json.loads((ROOT.parent/'caocaozhuan-remake/data/saves/slot-08.json').read_text(encoding='utf-8'))
    occupied = {row['y']*20+row['x'] for row in save['actors']}
    for row in fixture['rows']:
        row['match'] = row['accepted']==[index not in occupied and costs[row['slot']][terrain]!=255
                                       for index,terrain in enumerate(save['terrain'])]
    for row in fixture['synthetic']:
        row['match'] = row['accepted']==(row['state']==1 and costs[row['slot']][row['terrain']]!=255)
    total = len(fixture['rows'])*640+len(fixture['synthetic'])
    matched = sum(640 for row in fixture['rows'] if row['match'])+sum(row['match'] for row in fixture['synthetic'])
    result = {'function':'0x4401A8','total':total,'matched':matched,**fixture}
    (ROOT/'analysis/native-movement-destinations.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f'Native movement destinations: {matched}/{total}')
    if total!=25280 or matched!=total:
        raise SystemExit('Destination acceptance mismatch')
finally:
    device.kill(pid)
    if session:
        session.detach()
