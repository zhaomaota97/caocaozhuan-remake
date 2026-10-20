"""Run native counterattack eligibility and capture its recursive dispatch."""
import ast
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]
tree = ast.parse((ROOT / 'tools/export_slot08_native_health.py').read_text(encoding='utf-8'))
sources = [n.args[0].value for n in ast.walk(tree) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Attribute) and n.func.attr == 'create_script'
           and isinstance(n.args[0], ast.Constant)]
assert len(sources) == 1 and sources[0].count('return out;') == 1
source = sources[0].replace('return out;', r'''
 let calls=[];
 const recurse=new NativeCallback((action,a,d)=>{calls.push([a,d]);},'void',['pointer','uint8','uint8'],'thiscall');
 const face=new NativeCallback(()=>{},'void',['uint8','uint8'],'mscdecl');
 Interceptor.replace(b.add(0x64f1),recurse);Interceptor.replace(b.add(0x35829),face);Interceptor.flush();
 const gate=new NativeFunction(b.add(0x639a),'void',['pointer'],'fastcall');
 const action=Memory.alloc(0x620),rows=[];
 const arow=out.find(row=>row.slot<35),drow=out.find(row=>row.slot>=35);
 if(!arow||!drow)throw new Error('Need opposing saved actors');
 const a=b.add(0xb2c50+arow.slot*36),d=b.add(0xb2c50+drow.slot*36);
 const au=b.add(0xa1b68+a.readU32()*72),du=b.add(0xa1b68+d.readU32()*72);
 // Controlled weapons/accessories retain native category and range lookup.
 for(const u of [au,du])for(let slot=0;slot<3;slot++)u.add(0x2e+slot*3).writeU8(255);
 // Synthetic accessory entries isolate categories absent as accessories in Data.e5.
 const revenge=102,prevent=103;
 b.add(0xa1140+revenge*25+17).writeU8(40);
 b.add(0xa1140+prevent*25+17).writeU8(44);
 // Class 0 uses the native cardinal-neighbor attack range.
 du.add(0x2b).writeU8(0);
 for(const depth of [0,1,2])for(const hp of [0,100])for(const status of [0,8])
 for(const revengeOn of [false,true])for(const preventOn of [false,true])for(const distance of [1,5]){
  a.add(6).writeU8(10);a.add(7).writeU8(10);d.add(6).writeU8(10+distance);d.add(7).writeU8(10);
  battlefield.add(0xc80).writeByteArray(new Uint8Array(640).fill(255));
  battlefield.add(0xc80+210).writeU8(arow.slot);battlefield.add(0xc80+210+distance).writeU8(drow.slot);
  a.add(16).writeU32(100);d.add(16).writeU32(hp);d.add(30).writeU8(status);
  au.add(0x34).writeU8(preventOn?prevent:255);du.add(0x34).writeU8(revengeOn?revenge:255);
  action.writeByteArray(new Uint8Array(0x620));action.writeU8(arow.slot);action.add(16).writeU8(drow.slot);
  action.add(8).writePointer(au);action.add(12).writePointer(a);
  b.add(0x92e04).writeU8(depth);b.add(0x8ecd4).writeU32(7);calls=[];
  gate(action);
  rows.push({depth,hp,status,revengeOn,preventOn,distance,calls,finalDepth:b.add(0x92e04).readU8(),state:b.add(0x8ecd4).readU32()});
 }
 return {attacker:arow.slot,defender:drow.slot,revenge,prevent,rows};
''')

device = frida.get_local_device()
pid = device.spawn([str(ROOT / 'analysis/runtime-game/Ekd5.exe')], cwd=str(ROOT / 'analysis/runtime-game'))
session = None
try:
    session = device.attach(pid)
    script = session.create_script(source)
    script.load()
    data = dict(entries(ROOT / 'Data.e5'))
    result = script.exports_sync.read(list(data[0]), list(data[1]), list(data[3]), list(data[4]),
        list((ROOT / 'Sv08d.e5s').read_bytes()[0x14dc:]),
        list((ROOT / 'Sv08s.e5s').read_bytes()[1301:4291]),
        list((ROOT / 'analysis/saved-battlefields/Sv08s-terrain.bin').read_bytes()))
    for row in result['rows']:
        eligible = (row['depth'] < 2 and (row['depth'] == 0 or row['revengeOn'])
                    and row['hp'] > 0 and not row['status'] & 8
                    and not row['preventOn'] and row['distance'] == 1)
        reset = row['depth'] >= 2 or (row['depth'] != 0 and not row['revengeOn'])
        expected_depth = 0 if reset else row['depth'] + int(eligible)
        row['match'] = (row['calls'] == ([[result['defender'], result['attacker']]] if eligible else [])
                        and row['finalDepth'] == expected_depth and row['state'] == 7)
    (ROOT / 'analysis/native-counterattack-gate.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    matched = sum(row['match'] for row in result['rows'])
    print(f'Native counterattack gate: {matched}/{len(result["rows"])}')
    if matched != len(result['rows']):
        raise SystemExit('Counterattack mismatch')
finally:
    device.kill(pid)
    if session:
        session.detach()
