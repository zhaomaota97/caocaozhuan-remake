"""Cross-check native unit, weapon and armor XP award calculators."""
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
 const unitXp=new NativeFunction(b.add(0x379b),'uint',['pointer','uint'],'thiscall');
 const weaponXp=new NativeFunction(b.add(0x397d),'uint',['pointer','uint'],'thiscall');
 const armorXp=new NativeFunction(b.add(0x3a85),'uint',['pointer','uint'],'thiscall');
 const a=b.add(0xb2c50+out[0].slot*36),d=b.add(0xb2c50+out[1].slot*36);
 const au=b.add(0xa1b68+a.readU32()*72),du=b.add(0xa1b68+d.readU32()*72);
 for(const u of [au,du])for(let slot=0;slot<3;slot++)u.add(0x2e+slot*3).writeU8(255);
 // Controlled multiplier accessory; native classification and getter remain live.
 b.add(0xa1140+103*25+17).writeU8(31);b.add(0xa1140+103*25+21).writeU8(20);
 let ranged=0;
 for(let id=0;id<104;id++)if(b.add(0xa1140+id*25+17).readU8()===10){ranged=id;break;}
 const action=Memory.alloc(0x620);action.writeByteArray(new Uint8Array(0x620));
 action.add(1).writeU8(out[1].slot);action.add(8).writePointer(au);d.add(16).writeU32(100);
 const rows=[];
 for(const attackerLevel of [1,2,9,10,20,49,50])for(const defenderLevel of [1,2,9,10,20,49,50])
 for(const enabled of [false,true])for(const leader of [false,true])for(const affiliation of [0,1])
 for(const damage of [0,1,100])for(const mpDamage of [0,1])for(const rangedWeapon of [false,true])for(const multiplier of [10,20]){
  au.add(0x2c).writeU8(attackerLevel);du.add(0x2c).writeU8(defenderLevel);
  au.add(0x2e).writeU8(rangedWeapon?ranged:0);au.add(0x34).writeU8(multiplier===20?103:255);
  du.add(0x34).writeU8(multiplier===20?103:255);d.add(5).writeU8(affiliation);
  b.add(0x92f90+0x3d06).writeU16(leader?d.readU32():65535);
  action.add(0x600).writeU32(enabled?1:0);action.add(0x84).writeU32(damage);action.add(0x254).writeU32(mpDamage);
  b.add(0x8ecd4).writeU32(7);
  rows.push({attackerLevel,defenderLevel,enabled,leader,affiliation,damage,mpDamage,rangedWeapon,multiplier,
    unit:unitXp(action,0),weapon:weaponXp(action,0),armor:armorXp(action,0),state:b.add(0x8ecd4).readU32()});
 }
 return {ranged,rows};
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
        delta = row['defenderLevel'] - row['attackerLevel']
        if row['damage'] >= 100:
            base = min(200,32+delta*8) if delta > 0 else max(10,32+delta*4)
            base *= 2 if row['leader'] else 1
        else:
            base = min(100,8+delta*2) if delta > 0 else max(1,8+delta)
        unit = base*row['multiplier']//10 if row['enabled'] else 0
        damaged = row['damage'] != 0 or row['mpDamage'] != 0
        weapon = ((2 if delta < 0 else 3) if damaged else 1)*row['multiplier']//10
        if not row['enabled'] or row['rangedWeapon']:
            weapon = 0
        armor = ((3 if delta > 0 else 4) if damaged else 1)*row['multiplier']//10
        if row['affiliation'] != 0:
            armor = 0
        row['match'] = row['unit'] == unit and row['weapon'] == weapon and row['armor'] == armor and row['state'] == 7
    (ROOT / 'analysis/native-attack-experience-awards.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    matched = sum(row['match'] for row in result['rows'])
    print(f'Native attack XP awards: {matched}/{len(result["rows"])}')
    if matched != len(result['rows']):
        print(next(row for row in result['rows'] if not row['match']))
        raise SystemExit('Attack XP award mismatch')
finally:
    device.kill(pid)
    if session:
        session.detach()
