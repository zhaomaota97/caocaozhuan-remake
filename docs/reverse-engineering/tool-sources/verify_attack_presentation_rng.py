"""Execute native 0x405744 with UI leaves stubbed; verify its RNG boundary."""
import ast
import json
from pathlib import Path

import frida
from export_map_layouts import entries
from game_rng import GameRng

ROOT = Path(__file__).resolve().parents[1]
tree = ast.parse((ROOT / 'tools/export_slot08_native_health.py').read_text(encoding='utf-8'))
sources = [n.args[0].value for n in ast.walk(tree) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Attribute) and n.func.attr == 'create_script'
           and isinstance(n.args[0], ast.Constant)]
assert len(sources) == 1 and sources[0].count('return out;') == 1
source = sources[0].replace('return out;', r'''
 const callbacks=[];let dialogue=0;
 function stub(rva,args,abi,fn=()=>{}){
  const cb=new NativeCallback(fn,'void',args,abi);callbacks.push(cb);
  Interceptor.replace(b.add(rva),cb);
 }
 stub(0x3b8f,['pointer'],'fastcall');
 stub(0x35829,['uint8','uint8'],'mscdecl');
 stub(0x3d85,['pointer','uint'],'thiscall');
 stub(0x55123,['pointer','uint8','uint8','uint'],'thiscall');
 stub(0xc02f,['pointer','int'],'mscdecl');
 stub(0x3fcc9,['pointer'],'fastcall');
 stub(0x5965d,['pointer','uint'],'mscdecl',()=>{dialogue++;});
 stub(0x44e9,[],'mscdecl');
 Interceptor.flush();
 const animate=new NativeFunction(b.add(0x5744),'void',['pointer'],'fastcall');
 const action=Memory.alloc(0x620);action.writeByteArray(new Uint8Array(0x620));
 action.writeU8(out[0].slot);action.add(16).writeU8(out[1].slot);
 action.add(12).writePointer(b.add(0xb2c50+out[0].slot*36));
 const rows=[];
 for(const critical of [0,1])for(let seed=0;seed<256;seed++){
  action.add(0x604).writeU32(critical);b.add(0x8ecd4).writeU32(seed);dialogue=0;
  animate(action);
  rows.push({critical:!!critical,seed,state:b.add(0x8ecd4).readU32(),dialogue,
    target:action.add(1).readU8()});
 }
 return {rows,primaryTarget:out[1].slot};
''')

device = frida.get_local_device()
pid = device.spawn([str(ROOT / 'analysis/runtime-game/Ekd5.exe')], cwd=str(ROOT / 'analysis/runtime-game'))
session = None
try:
    session = device.attach(pid)
    script = session.create_script(source)
    script.load()
    data = dict(entries(ROOT / 'Data.e5'))
    result = script.exports_sync.read(
        list(data[0]), list(data[1]), list(data[3]), list(data[4]),
        list((ROOT / 'Sv08d.e5s').read_bytes()[0x14dc:]),
        list((ROOT / 'Sv08s.e5s').read_bytes()[1301:4291]),
        list((ROOT / 'analysis/saved-battlefields/Sv08s-terrain.bin').read_bytes()))
    for row in result['rows']:
        rng = GameRng(row['seed'])
        expected_dialogue = int(rng.chance(25)) if row['critical'] else 0
        row['match'] = (row['state'] == rng.state and row['dialogue'] == expected_dialogue
                        and row['target'] == result['primaryTarget'])
    result['scope'] = 'Native 0x405744; animation/camera/dialogue leaves stubbed. Does not validate rendering or random draws inside those leaves.'
    path = ROOT / 'analysis/native-attack-presentation-rng.json'
    path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    matched = sum(row['match'] for row in result['rows'])
    print(f'Native presentation RNG and dialogue dispatch: {matched}/{len(result["rows"])}')
    if matched != len(result['rows']):
        raise SystemExit('Presentation RNG mismatch')
finally:
    device.kill(pid)
    if session:
        session.detach()
