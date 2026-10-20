"""Capture the original movement sound selector with the audio playback sink replaced."""
import ast
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]
tree = ast.parse((ROOT/'tools/export_slot08_native_health.py').read_text(encoding='utf-8'))
sources = [node.args[0].value for node in ast.walk(tree)
           if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
           and node.func.attr == 'create_script' and isinstance(node.args[0], ast.Constant)]
if len(sources) != 1 or sources[0].count('return out;') != 1:
    raise RuntimeError('Review native initialization before reuse')
source = sources[0].replace('return out;', '''
 let calls=[];
 const sink=new NativeCallback((self,id,mode)=>{calls.push({id,mode});},
  'void',['pointer','int','int'],'thiscall');
 Interceptor.replace(b.add(0x7467a),sink);Interceptor.flush();
 const select=new NativeFunction(b.add(0x3f38b),'void',['uint8','uint','uint8'],'mscdecl');
 const rows=[];
 for(let kind=0;kind<32;kind++)for(let terrain=0;terrain<30;terrain++){
  battlefield.add(0x640).writeU8(terrain);calls=[];select(kind,0,0);
  rows.push({movementType:kind,terrain,calls});
 }
 return rows;
''')
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
        kind, terrain = row['movementType'], row['terrain']
        sound = {2:27,7:26,9:29,13:29,10:28}.get(terrain)
        if sound is None:
            sound = 24 if kind in (0,3,4,11,13) else 25 if kind in (5,21,22) else 23
        expected = [] if kind == 20 else [{'id':sound,'mode':0}]
        row['expected'] = expected
        row['match'] = row['calls'] == expected
    result = {'selector':'0x43F38B','playbackSink':'0x47467A',
              'total':len(rows),'matched':sum(row['match'] for row in rows),'rows':rows}
    (ROOT/'analysis/native-movement-sounds.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f"Native movement sounds: {result['matched']}/{result['total']}")
    if result['matched'] != result['total']:
        raise SystemExit('Sound selector mismatch')
finally:
    device.kill(pid)
    if session:
        session.detach()
