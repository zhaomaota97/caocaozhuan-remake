"""Probe native movement-budget branches independently of the slot08 snapshot."""
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]
data = dict(entries(ROOT / 'Data.e5'))
device = frida.get_local_device()
pid = device.spawn([str(ROOT / 'analysis/runtime-game/Ekd5.exe')],
                   cwd=str(ROOT / 'analysis/runtime-game'))
session = None
try:
    session = device.attach(pid)
    script = session.create_script('''
rpc.exports={probe(source,classes,roster,actors,items){
 const b=Process.mainModule.base;
 function buf(bytes){const p=Memory.alloc(bytes.length);p.writeByteArray(bytes);return p;}
 const loadClass=new NativeFunction(b.add(0x93ef),'pointer',['pointer','pointer'],'thiscall');
 let input=buf(classes);
 for(let i=0;i<53;i++)input=loadClass(b.add(0xabfa0+i*27),input);
 const expand=new NativeFunction(b.add(0x8be3),'pointer',['pointer','uint16','pointer','int'],'thiscall');
 const loadUnit=new NativeFunction(b.add(0x9188),'pointer',['pointer','pointer'],'thiscall');
 const loadActor=new NativeFunction(b.add(0x42e26),'pointer',['pointer','pointer'],'thiscall');
 const unit=b.add(0xa1b68),actor=b.add(0xb2c50);
 expand(unit,0,buf(source),0);loadUnit(unit,buf(roster));loadActor(actor,buf(actors));
 actor.writeU32(0);
 for(let slot=0;slot<3;slot++)unit.add(0x2e+slot*3).writeU8(255);
 const budget=new NativeFunction(b.add(0x3f74f),'uint8',['pointer'],'fastcall');
 const rows=[];
 for(let classId=0;classId<53;classId++){
  unit.add(0x2b).writeU8(classId);
  for(const status of [0,1,2,3,4,255])for(const tier of [0,1,2,3,4,5,254,255]){
   actor.add(30).writeU8(status);actor.add(29).writeU8(tier);
   rows.push({classId,statusFlags:status,movementTier:tier,native:budget(actor)});
  }
 }
 const loadItem=new NativeFunction(b.add(0xc537),'pointer',['pointer','pointer'],'thiscall');
 const itemInput=buf(items);
 for(let i=0;i<104;i++)loadItem(b.add(0xa1140+i*25),itemInput.add(i*25));
 unit.add(0x2b).writeU8(0);actor.add(30).writeU8(0);actor.add(29).writeU8(3);
 const equipment=[];
 function clear(){for(let slot=0;slot<3;slot++)unit.add(0x2e+slot*3).writeU8(255);}
 for(let id=0;id<104;id++)for(let slot=0;slot<3;slot++){
  clear();unit.add(0x2e+slot*3).writeU8(id);
  equipment.push({kind:'original-item',itemId:id,slot,native:budget(actor)});
 }
 // Synthetic item records exercise arithmetic boundaries absent from actual items.
 const record=b.add(0xa1140);
 for(const category of [0,1,2,17,18,32,33])for(const value of [0,1,127,254,255]){
  record.add(17).writeU8(category);record.add(20).writeU8(32);
  record.add(21).writeU8(value);record.add(22).writeU8(value);
  for(const slots of [[0],[1],[2],[0,1],[0,1,2]]){
   clear();for(const slot of slots)unit.add(0x2e+slot*3).writeU8(0);
   equipment.push({kind:'synthetic-item',category,value,slots,native:budget(actor)});
  }
 }
 return {rows,equipment};
}};
''')
    script.load()
    probes = script.exports_sync.probe(list(data[0][:32]), list(data[3]),
        list((ROOT/'Sv08d.e5s').read_bytes()[0x14dc:0x14fc]),
        list((ROOT/'Sv08s.e5s').read_bytes()[1301:1327]), list(data[1]))
    rows = probes['rows']
    for row in rows:
        base = data[3][row['classId'] * 27]
        expected = (0 if row['statusFlags'] & 2 else
                    min(255, base + 2) if row['movementTier'] >= 4 else
                    max(0, base - 1) if row['movementTier'] < 3 else base)
        row['expected'] = expected
        row['match'] = row['native'] == expected
    result = {'function': '0x43F74F', 'equipment': 'all three slots empty (255)',
              'total': len(rows), 'matched': sum(row['match'] for row in rows), 'rows': rows}
    (ROOT/'analysis/native-movement-budget-branches.json').write_text(
        json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(f"Native movement-budget branches: {result['matched']}/{result['total']}")
    if result['matched'] != result['total']:
        raise SystemExit('Native movement-budget mismatch; inspect exported rows')
    equipment = probes['equipment']
    for row in equipment:
        bonus = 0
        slots = [row['slot']] if row['kind'] == 'original-item' else row['slots']
        for slot in slots:
            if row['kind'] == 'original-item':
                record = data[1][row['itemId']*25:(row['itemId']+1)*25]
                category, effect, primary, secondary = record[17], record[18], record[21], record[22]
            else:
                category, effect = row['category'], 32
                primary = secondary = row['value']
            if category == 32:
                bonus = (bonus + primary) & 255
            if slot < 2 and category < 18 and category & 1 and effect == 32:
                bonus = (bonus + secondary) & 255
        row['expected'] = min(255, data[3][0] + bonus)
        row['match'] = row['expected'] == row['native']
    equip_result = {'function': '0x43F74F', 'classId': 0, 'statusFlags': 0,
                    'movementTier': 3, 'total': len(equipment),
                    'matched': sum(row['match'] for row in equipment), 'rows': equipment}
    (ROOT/'analysis/native-movement-budget-equipment.json').write_text(
        json.dumps(equip_result, indent=2)+'\n', encoding='utf-8')
    print(f"Native equipment movement budgets: {equip_result['matched']}/{equip_result['total']}")
    if equip_result['matched'] != equip_result['total']:
        raise SystemExit('Native equipment mismatch; inspect exported rows')
finally:
    device.kill(pid)
    if session:
        session.detach()
