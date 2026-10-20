"""Validate exported treasure fields against original native getters."""
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]
catalog=json.loads((ROOT.parent/'caocaozhuan-remake/data/mappings/treasure-catalog.json').read_text(encoding='utf-8'))
data=dict(entries(ROOT/'Data.e5'))
device=frida.get_local_device()
pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'))
session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={verify(items,classes,rows){
 const b=Process.mainModule.base;
 const get=(rva,type,abi,args)=>new NativeFunction(b.add(rva),type,args,abi);
 const decode=get(0xc537,'pointer','thiscall',['pointer','pointer']);
 const permission=get(0x95c0,'uint','thiscall',['pointer','int']);
 const icon=get(0x72c70,'uint8','fastcall',['pointer']);
 const price=get(0xe070,'uint','fastcall',['pointer']);
 const membership=get(0x9600,'uint8','fastcall',['pointer']);
 const input=Memory.alloc(items.length);input.writeByteArray(items);
 const cls=Memory.alloc(classes.length);cls.writeByteArray(classes);
 return rows.map(row=>{
  const obj=Memory.alloc(25);decode(obj,input.add(row.itemId*25));
  const category=obj.add(17).readU8(),restriction=obj.add(23).readU8();
  const groups=Array.from({length:13},(_,group)=>category<18?Boolean(permission(cls.add(group*3*27),category)&255):restriction===255||restriction===group);
  return {itemId:row.itemId,iconIndex:icon(obj),membership:membership(obj),price:obj.add(18).readU8()===255?null:price(obj),equipGroups:groups};
 });
}};
''')
    script.load()
    observed=script.exports_sync.verify(list(data[1]),list(data[3]),catalog['entries'])
    expected={row['itemId']:row for row in catalog['entries']}
    for row in observed:
        target=expected[row['itemId']]
        row['match']=all(row[key]==target[key] for key in ('iconIndex','price','equipGroups')) and row['membership']==target['membershipByte']
    result={'rows':observed,'passed':len(observed)==50 and all(row['match'] for row in observed)}
    (ROOT/'analysis/native-treasure-catalog-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f"Native treasure records: {sum(row['match'] for row in observed)}/{len(observed)}; permissions={len(observed)*13}")
    if not result['passed']:raise SystemExit(1)
finally:
    device.kill(pid)
    if session:
        try:session.detach()
        except frida.InvalidOperationError:pass
