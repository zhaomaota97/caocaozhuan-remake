"""Check native equipment XP updates across item definitions and boundaries."""
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
 let notifications=0;
 // Caller pushes two arguments then adds ESP,8: cdecl despite Ghidra's inferred fastcall.
 const notify=new NativeCallback(()=>{notifications++;},'void',['uint','uint8'],'mscdecl');
 Interceptor.replace(b.add(0x83ef),notify);Interceptor.flush();
 const grant=new NativeFunction(b.add(0x82d6),'void',['pointer','uint8','int'],'thiscall');
 const special=new NativeFunction(b.add(0xc76e),'uint',['uint'],'fastcall');
 const u=b.add(0xa1b68),rows=[],definitions=[];
 for(const id of [...Array.from({length:104},(_,i)=>i),255]){
  const cap=id===255?null:(special(b.add(0xa1140+id*25).toUInt32())?9:3);
  definitions.push({id,cap});
  for(const slot of [0,1,2])for(const level of [0,2,3,8,9])for(const xp of [0,99,255])for(const gain of [0,1,100,255]){
   u.add(0x2e+slot*3).writeU8(id);u.add(0x2f+slot*3).writeU8(level);u.add(0x30+slot*3).writeU8(xp);
   notifications=0;b.add(0x8ecd4).writeU32(7);
   try{grant(u,slot,gain);}catch(error){throw new Error(JSON.stringify({id,slot,level,xp,gain})+': '+error);}
   rows.push({id,slot,level,xp,gain,finalLevel:u.add(0x2f+slot*3).readU8(),
    finalXp:u.add(0x30+slot*3).readU8(),notifications,state:b.add(0x8ecd4).readU32()});
  }
 }
 return {definitions,rows};
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
    caps = {row['id']:row['cap'] for row in result['definitions']}
    for item_id in range(104):
        category = data[1][item_id * 25 + 17]
        assert caps[item_id] == (9 if category < 18 and category & 1 else 3), item_id
    for row in result['rows']:
        level, xp, count = row['level'], row['xp'], 0
        if row['slot'] < 2 and row['id'] != 255:
            xp += row['gain']
            while xp >= 100 and level < caps[row['id']]:
                level += 1
                xp -= 100
                count += 1
            xp = xp if level < caps[row['id']] else 255
        row['match'] = (row['finalLevel'] == level and row['finalXp'] == xp
                        and row['notifications'] == count and row['state'] == 7)
    (ROOT / 'analysis/native-equipment-experience.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    matched = sum(row['match'] for row in result['rows'])
    print(f'Native equipment XP/levels/notifications: {matched}/{len(result["rows"])}')
    if matched != len(result['rows']):
        raise SystemExit('Equipment XP mismatch')
finally:
    device.kill(pid)
    if session:
        session.detach()
