"""Validate native item-level attribute contribution for all original items."""
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]
device = frida.get_local_device()
pid = device.spawn([str(ROOT / 'analysis/runtime-game/Ekd5.exe')], cwd=str(ROOT / 'analysis/runtime-game'))
session = None
try:
    session = device.attach(pid)
    script = session.create_script('''
rpc.exports={capture(bytes){
 const b=Process.mainModule.base,input=Memory.alloc(bytes.length);input.writeByteArray(bytes);
 const load=new NativeFunction(b.add(0xc537),'pointer',['pointer','pointer'],'thiscall');
 const value=new NativeFunction(b.add(0xc674),'uint8',['pointer','uint'],'thiscall');
 const definitions=[],rows=[];
 for(let id=0;id<104;id++){
  const item=b.add(0xa1140+id*25);load(item,input.add(id*25));
  definitions.push({id,categoryByte:item.add(17).readU8(),baseValue:item.add(21).readU8(),growthValue:item.add(23).readU8()});
  for(const level of [0,1,2,3,8,9,10,49,99,255])rows.push({id,level,result:value(item,level)});
 }
 return {definitions,rows};
}};
''')
    script.load()
    result = script.exports_sync.capture(list(dict(entries(ROOT / 'Data.e5'))[1]))
    failures = []
    for row in result['rows']:
        item = result['definitions'][row['id']]
        expected = min(255, item['baseValue'] + max(0, row['level']-1)*item['growthValue']) if item['categoryByte'] < 18 else item['baseValue']
        if row['result'] != expected:
            failures.append(dict(row, expected=expected))
    result.update(passed=not failures, address='0x40C674', scope='Original 104 definitions; single-item contribution, not complete equipment aggregation')
    text = json.dumps(result, indent=2)+'\n'
    (ROOT / 'analysis/native-equipment-attribute.json').write_text(text, encoding='utf-8')
    (ROOT.parent / 'caocaozhuan-remake/docs/reverse-engineering/native-equipment-attribute.json').write_text(text, encoding='utf-8')
    print(f'Native equipment attributes: {len(result["rows"])-len(failures)}/{len(result["rows"])}')
    if failures:
        raise RuntimeError(failures[0])
finally:
    device.kill(pid)
    if session:
        session.detach()
