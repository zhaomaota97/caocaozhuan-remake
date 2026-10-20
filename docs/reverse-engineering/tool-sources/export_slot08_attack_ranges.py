"""Export original class/equipment attack ranges using the saved battle initialization."""
import ast
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]
tree=ast.parse((ROOT/'tools/export_slot08_native_health.py').read_text(encoding='utf-8'))
sources=[node.args[0].value for node in ast.walk(tree)
         if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
         and node.func.attr=='create_script' and isinstance(node.args[0],ast.Constant)]
if len(sources)!=1 or sources[0].count('return out;')!=1:
    raise RuntimeError('Review native initialization before reuse')
source=sources[0].replace('return out;', '''
 const range=new NativeFunction(b.add(0x3f8be),'uint8',['pointer','uint'],'fastcall');
 const attack=new NativeFunction(b.add(0x3f4fe),'uint',['pointer'],'fastcall');
 const defense=new NativeFunction(b.add(0x3f595),'uint',['pointer'],'fastcall');
 const adaptation=new NativeFunction(b.add(0x3f84d),'uint',['pointer'],'fastcall');
 return out.map(row=>({slot:row.slot,classId:row.classId,equipmentSlots:row.equipmentSlots,
  nativeRange:range(b.add(0xb2c50+row.slot*36),0),
  nativeAttack:attack(b.add(0xb2c50+row.slot*36)),nativeDefense:defense(b.add(0xb2c50+row.slot*36)),
  terrainAdaptation:adaptation(b.add(0xb2c50+row.slot*36))&255}));
''')
data=dict(entries(ROOT/'Data.e5'))
device=frida.get_local_device()
pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'))
session=None
try:
    session=device.attach(pid)
    script=session.create_script(source);script.load()
    rows=script.exports_sync.read(list(data[0]),list(data[1]),list(data[3]),list(data[4]),
        list((ROOT/'Sv08d.e5s').read_bytes()[0x14dc:]),
        list((ROOT/'Sv08s.e5s').read_bytes()[1301:4291]),
        list((ROOT/'analysis/saved-battlefields/Sv08s-terrain.bin').read_bytes()))
    for row in rows:
        value=data[3][row['classId']*27+1]
        for slot in row['equipmentSlots']:
            if slot['itemId']==255:
                continue
            record=data[1][slot['itemId']*25:(slot['itemId']+1)*25]
            if slot['slot']<2 and record[17]<18 and record[17]&1 and record[18]==42:
                value=record[22]
            if slot['slot']==2 and record[17]==42:
                value=record[21]
        row['expectedRange']=value
        row['match']=value==row['nativeRange']
    result={'function':'0x43F8BE','total':len(rows),'matched':sum(row['match'] for row in rows),'rows':rows}
    (ROOT/'analysis/native-slot08-attack-ranges.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f"Native slot08 attack ranges: {result['matched']}/{result['total']}")
    if result['matched']!=len(rows):
        raise SystemExit('Range mismatch')
    remake=ROOT.parent/'caocaozhuan-remake'
    (remake/'data/rules/class-attack-ranges.json').write_text(json.dumps([
        {'id':i,'range':data[3][i*27+1]} for i in range(53)],indent=2)+'\n',encoding='utf-8')
    (remake/'data/mappings/slot08-attack-ranges.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (remake/'data/mappings/slot08-combat-attributes.json').write_text(json.dumps({
        'getters':{'attack':'0x43F4FE','defense':'0x43F595','terrainAdaptation':'0x43F84D'},
        'scope':'native getters at saved coordinates; not a complete attack resolution',
        'actors':[{'id':f"unit-{row['slot']}",'attack':row['nativeAttack'],
                   'defense':row['nativeDefense'],'terrainAdaptation':row['terrainAdaptation']} for row in rows]
    },indent=2)+'\n',encoding='utf-8')
finally:
    device.kill(pid)
    if session:
        session.detach()
