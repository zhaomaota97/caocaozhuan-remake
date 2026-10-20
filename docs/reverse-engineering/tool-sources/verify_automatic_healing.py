"""Native damage writeback through automatic bean use, with UI leaves replaced."""
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
 const callbacks=[];let uses=0;
 function stub(rva,args,abi,fn=()=>{}){
  const cb=new NativeCallback(fn,'void',args,abi);callbacks.push(cb);Interceptor.replace(b.add(rva),cb);
 }
 stub(0x50984,['uint8','uint8','int','int','uint','uint','uint','int'],'mscdecl');
 stub(0x82d6,['pointer','uint8','int'],'thiscall');
 stub(0x55123,['pointer','uint8','uint8','uint'],'thiscall');
 stub(0x79a01,['uint'],'mscdecl');
 // Native animation marks the action successful at its end; preserve that side effect.
 stub(0x1c762,['pointer','int8'],'thiscall',obj=>{obj.add(0x1c).writeU32(1);uses++;});
 Interceptor.flush();
 const write=new NativeFunction(b.add(0x5889),'void',['pointer'],'fastcall');
 const action=Memory.alloc(0x620),a=b.add(0xb2c50+out[0].slot*36),d=b.add(0xb2c50+out[1].slot*36);
 const au=b.add(0xa1b68+a.readU32()*72),du=b.add(0xa1b68+d.readU32()*72);
 for(const u of [au,du])for(let slot=0;slot<3;slot++)u.add(0x2e+slot*3).writeU8(255);
 au.add(0x2b).writeU8(0);
 // Synthetic accessory isolates effect 62; actual bean entry 87 remains unchanged.
 b.add(0xa1140+103*25+17).writeU8(62);
 const bean=b.add(0xa1140+87*25),capacity=out[1].maxHp,rows=[];
 for(const equipped of [false,true])for(const affiliation of [0,1])for(const stock of [0,1,2])
 for(const hp of [1,capacity-1,capacity])for(const damage of [0,1,30]){
  if(damage>hp)continue;
  d.add(5).writeU8(affiliation);d.add(16).writeU32(hp);d.add(30).writeU8(0);d.add(13).writeU8(32);
  du.add(0x34).writeU8(equipped?103:255);b.add(0xb0770+0x26b).writeU8(stock);
  action.writeByteArray(new Uint8Array(0x620));action.writeU8(out[0].slot);
  action.add(8).writePointer(au);action.add(12).writePointer(a);
  action.add(16).writeByteArray(new Uint8Array(116).fill(255));action.add(16).writeU8(out[1].slot);
  action.add(0x84).writeU32(damage);uses=0;b.add(0x8ecd4).writeU32(7);
  write(action);
  rows.push({equipped,affiliation,stock,hp,damage,uses,finalHp:d.add(16).readU32(),
    finalStock:b.add(0xb0770+0x26b).readU8(),flags:d.add(13).readU8(),state:b.add(0x8ecd4).readU32()});
 }
 return {capacity,beanCategory:bean.add(17).readU8(),beanAmount:bean.add(21).readU8(),rows};
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
    assert result['beanCategory'] == 63
    for row in result['rows']:
        remaining = row['hp'] - row['damage']
        use = (row['equipped'] and row['damage'] > 0 and remaining > 0
               and (row['affiliation'] != 0 or row['stock'] > 0))
        expected_hp = min(result['capacity'], remaining + result['beanAmount']) if use else remaining
        expected_stock = row['stock'] - int(use and row['affiliation'] == 0)
        row['match'] = (row['uses'] == int(use) and row['finalHp'] == expected_hp
                        and row['finalStock'] == expected_stock and row['flags'] == 0 and row['state'] == 7)
    (ROOT / 'analysis/native-automatic-healing.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    matched = sum(row['match'] for row in result['rows'])
    print(f'Native automatic healing/writeback/inventory: {matched}/{len(result["rows"])}; bean={result["beanAmount"]}')
    if matched != len(result['rows']):
        raise SystemExit('Automatic healing mismatch')
finally:
    device.kill(pid)
    if session:
        session.detach()
