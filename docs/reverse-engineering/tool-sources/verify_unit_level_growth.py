"""Execute native unit XP writeback and growth across classes and rank boundaries."""
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
 let refreshes=0;
 const refresh=new NativeCallback(()=>{refreshes++;},'void',['uint'],'mscdecl');
 Interceptor.replace(b.add(0x79a01),refresh);Interceptor.flush();
 const grant=new NativeFunction(b.add(0x8950),'void',['pointer','uint','int'],'thiscall');
 const classes=Array.from({length:53},(_,id)=>({id,growth:Array.from(new Uint8Array(b.add(0xabfa0+id*27+2).readByteArray(7)))}));
 const actorBefore=Array.from(new Uint8Array(b.add(0xb2c50).readByteArray(115*36)));
 const rows=[];
 for(const classId of Array.from({length:53},(_,i)=>i))for(const id of [25,26])for(const level of [1,49,50])
 for(const rank of [24,25,34,35,44,45])for(const total of [0,99,100,199,500,1000])for(const nearCap of [false,true]){
  const u=b.add(0xa1b68+id*72);u.writeU16(id);u.add(0x2b).writeU8(classId);u.add(0x2c).writeU8(level);u.add(0x2d).writeU8(17);
  for(let i=0;i<5;i++){u.add(0x21+i).writeU8(rank);u.add(0x15+i).writeU8(nearCap?254:10);}
  u.add(0x1c).writeU32(nearCap?499:10);u.add(0x20).writeU8(nearCap?249:10);
  refreshes=0;b.add(0x8ecd4).writeU32(7);grant(u,total,0);
  rows.push({classId,id,level,rank,total,nearCap,finalLevel:u.add(0x2c).readU8(),xp:u.add(0x2d).readU8(),
    stats:[...Array.from(new Uint8Array(u.add(0x15).readByteArray(5))),u.add(0x1c).readU32(),u.add(0x20).readU8()],
    refreshes,state:b.add(0x8ecd4).readU32()});
 }
 const actorAfter=Array.from(new Uint8Array(b.add(0xb2c50).readByteArray(115*36)));
 return {classes,rows,actorsUnchanged:JSON.stringify(actorBefore)===JSON.stringify(actorAfter)};
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
        eligible = row['id'] < 26 and row['level'] < 50
        count = min(50-row['level'], row['total']//100) if eligible else 0
        level = row['level'] + count
        xp = (255 if level >= 50 else row['total'] % 100) if eligible else 17
        rank = row['rank']
        bonus = 1 if rank < 25 else 2 if rank < 35 else 3 if rank < 45 else 4
        growth = result['classes'][row['classId']]['growth']
        increments = [(value+bonus)//2 if i < 5 else value for i,value in enumerate(growth)]
        caps = [255]*5 + [500,250]
        initial = [254]*5+[499,249] if row['nearCap'] else [10]*7
        stats = [min(cap,value+increment*count) for value,increment,cap in zip(initial,increments,caps)]
        row['match'] = (row['finalLevel'] == level and row['xp'] == xp and row['stats'] == stats
                        and row['refreshes'] == int(eligible) and row['state'] == 7)
    (ROOT / 'analysis/native-unit-level-growth.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    matched = sum(row['match'] for row in result['rows'])
    assert result['actorsUnchanged'], 'Battle actor state changed'
    print(f'Native unit XP/level/growth: {matched}/{len(result["rows"])}')
    if matched != len(result['rows']):
        print(next(row for row in result['rows'] if not row['match']))
        raise SystemExit('Unit growth mismatch')
finally:
    device.kill(pid)
    if session:
        session.detach()
