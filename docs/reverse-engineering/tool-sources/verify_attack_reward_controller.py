"""Run the native attacker reward controller through XP and growth writebacks."""
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
 const callbacks=[];let notifications=0,refreshes=0;
 function stub(rva,args,abi,fn=()=>{}){
  const cb=new NativeCallback(fn,'void',args,abi);callbacks.push(cb);Interceptor.replace(b.add(rva),cb);
 }
 stub(0x50984,['uint8','uint8','int','int','uint','uint','uint','int'],'mscdecl');
 stub(0x79a01,['uint'],'mscdecl',()=>{refreshes++;});
 stub(0x83ef,['uint','uint8'],'mscdecl',()=>{notifications++;});
 const notVisible=new NativeCallback(()=>0,'int',[],'mscdecl');callbacks.push(notVisible);Interceptor.replace(b.add(0xb922),notVisible);
 stub(0x7467a,['pointer','int','int'],'thiscall');
 stub(0x2f699,['int'],'mscdecl');
 Interceptor.flush();
 const grant=new NativeFunction(b.add(0x5c6c),'void',['pointer'],'fastcall');
 const action=Memory.alloc(0x620);action.writeByteArray(new Uint8Array(0x620));
 const growth=Array.from(new Uint8Array(b.add(0xabfa0+2).readByteArray(7))),rows=[];
 // Class 0; real item 0 is a normal weapon with a level cap of 3.
 for(const id of [25,26])for(const level of [1,49,50])for(const xp of [0,99,255])for(const award of [0,1,100,250])
 for(const weaponLevel of [0,2,3])for(const weaponXp of [0,99,255])for(const weaponAward of [0,1,100,250]){
  const u=b.add(0xa1b68+id*72);u.writeU16(id);u.add(0x2b).writeU8(0);u.add(0x2c).writeU8(level);u.add(0x2d).writeU8(xp);
  for(let i=0;i<5;i++){u.add(0x15+i).writeU8(10);u.add(0x21+i).writeU8(25);}
  u.add(0x1c).writeU32(10);u.add(0x20).writeU8(10);
  u.add(0x2e).writeU8(0);u.add(0x2f).writeU8(weaponLevel);u.add(0x30).writeU8(weaponXp);
  u.add(0x31).writeU8(255);u.add(0x34).writeU8(255);
  action.add(8).writePointer(u);action.add(0x428).writeU32(award);action.add(0x42c).writeU32(weaponAward);
  notifications=0;refreshes=0;b.add(0x8ecd4).writeU32(7);grant(action);
  rows.push({id,level,xp,award,weaponLevel,weaponXp,weaponAward,finalLevel:u.add(0x2c).readU8(),
    finalXp:u.add(0x2d).readU8(),finalWeaponLevel:u.add(0x2f).readU8(),finalWeaponXp:u.add(0x30).readU8(),
    stats:[...Array.from(new Uint8Array(u.add(0x15).readByteArray(5))),u.add(0x1c).readU32(),u.add(0x20).readU8()],
    notifications,refreshes,state:b.add(0x8ecd4).readU32()});
 }
 return {growth,rows};
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
    assert data[1][17] == 0
    for row in result['rows']:
        eligible = row['id'] < 26 and row['level'] < 50
        total = row['xp'] + row['award']
        count = min(50-row['level'],total//100) if eligible else 0
        level = row['level'] + count
        xp = (255 if level >= 50 else total % 100) if eligible else row['xp']
        increments = [(v+2)//2 if i < 5 else v for i,v in enumerate(result['growth'])]
        stats = [min(cap,10+v*count) for cap,v in zip([255]*5+[500,250],increments)]
        wl, wx, notices = row['weaponLevel'], row['weaponXp']+row['weaponAward'], 0
        while wx >= 100 and wl < 3:
            wl += 1
            wx -= 100
            notices += 1
        wx = wx if wl < 3 else 255
        row['match'] = (row['finalLevel'] == level and row['finalXp'] == xp and row['stats'] == stats
                        and row['finalWeaponLevel'] == wl and row['finalWeaponXp'] == wx
                        and row['notifications'] == notices and row['refreshes'] == int(eligible) and row['state'] == 7)
    (ROOT / 'analysis/native-attack-reward-controller.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    matched = sum(row['match'] for row in result['rows'])
    print(f'Native attacker reward controller: {matched}/{len(result["rows"])}')
    if matched != len(result['rows']):
        print(next(row for row in result['rows'] if not row['match']))
        raise SystemExit('Reward controller mismatch')
finally:
    device.kill(pid)
    if session:
        session.detach()
