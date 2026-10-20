"""Check native 0x405E03 max-style reward aggregation with controlled targets."""
import ast
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]
tree=ast.parse((ROOT/'tools/export_slot08_native_health.py').read_text(encoding='utf-8'))
sources=[n.args[0].value for n in ast.walk(tree) if isinstance(n,ast.Call)
         and isinstance(n.func,ast.Attribute) and n.func.attr=='create_script'
         and isinstance(n.args[0],ast.Constant)]
assert len(sources)==1 and sources[0].count('return out;')==1
source=sources[0].replace('return out;',r'''
 const callbacks=[];
 function stub(rva,args,abi,fn=()=>{}){const cb=new NativeCallback(fn,'void',args,abi);callbacks.push(cb);Interceptor.replace(b.add(rva),cb);}
 stub(0x50984,['uint8','uint8','int','int','uint','uint','uint','int'],'mscdecl');
 stub(0x5889,['pointer'],'fastcall');stub(0x5c6c,['pointer'],'fastcall');
 const generateBattle=new NativeFunction(b.add(0x5e03),'void',['pointer'],'fastcall');
 const calcUnit=new NativeFunction(b.add(0x379b),'uint',['pointer','uint'],'thiscall');
 const calcWeapon=new NativeFunction(b.add(0x397d),'uint',['pointer','uint'],'thiscall');
 const calcArmor=new NativeFunction(b.add(0x3a85),'uint',['pointer','uint'],'thiscall');Interceptor.flush();
 const aggAction=Memory.alloc(0x620),aggActor=b.add(0xb2c50+out[0].slot*36),aggUnit=b.add(0xa1b68+aggActor.readU32()*72),aggRows=[];
 aggAction.writeByteArray(new Uint8Array(0x620));aggAction.add(12).writePointer(aggActor);aggAction.add(8).writePointer(aggUnit);
 for(const count of [1,2,3,5,10])for(const unitAwards of [0,1,17,100,255])for(const weaponAwards of [0,1,23,100,255])
 for(const armorAwards of [0,1,31,100,255]){
  aggAction.writeByteArray(new Uint8Array(0x620));aggAction.add(12).writePointer(aggActor);aggAction.add(8).writePointer(aggUnit);
  aggAction.add(16).writeByteArray(new Uint8Array(116).fill(255));
  for(let i=0;i<count;i++){aggAction.add(16+i).writeU8(out[(i+1)%out.length].slot);aggAction.add(0x428).writeU32(i===count-1?unitAwards:0);aggAction.add(0x42c).writeU32(i===count-1?weaponAwards:0);}
  aggAction.add(0x428).writeU32(unitAwards);aggAction.add(0x42c).writeU32(weaponAwards);aggAction.add(0x430).writeU32(armorAwards);
  aggAction.add(0x604).writeU32(0);generateBattle(aggAction);
  const expected=[];
  for(let i=0;i<count;i++){aggAction.add(1).writeU8(out[(i+1)%out.length].slot);expected.push({unit:calcUnit(aggAction,i),weapon:calcWeapon(aggAction,i),armor:calcArmor(aggAction,i)});}
  aggRows.push({count,unitAwards,weaponAwards,armorAwards,unitTotal:aggAction.add(0x428).readU32(),weaponTotal:aggAction.add(0x42c).readU32(),armorTotals:Array.from({length:count},(_,i)=>aggAction.add(0x430+i*4).readU32()),expected});
 }
 return {rows:aggRows};
''')
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
 session=device.attach(pid);script=session.create_script(source);script.load();data=dict(entries(ROOT/'Data.e5'))
 result=script.exports_sync.read(list(data[0]),list(data[1]),list(data[3]),list(data[4]),list((ROOT/'Sv08d.e5s').read_bytes()[0x14dc:]),list((ROOT/'Sv08s.e5s').read_bytes()[1301:4291]),list((ROOT/'analysis/saved-battlefields/Sv08s-terrain.bin').read_bytes()))
 for row in result['rows']:
  row['match']=(row['unitTotal']==max([row['unitAwards']]+[v['unit'] for v in row['expected']])
               and row['weaponTotal']==max([row['weaponAwards']]+[v['weapon'] for v in row['expected']])
               and row['armorTotals']==[v['armor'] for v in row['expected']])
 (ROOT/'analysis/native-multi-target-reward-aggregation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 matched=sum(r['match'] for r in result['rows']);print(f'Native multi-target reward aggregation: {matched}/{len(result["rows"])}')
 if matched!=len(result['rows']):raise SystemExit('Aggregation mismatch')
finally:
 device.kill(pid)
 if session:session.detach()
