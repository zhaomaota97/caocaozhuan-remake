"""Exercise real manual item dispatch, restoration, success gate and stock decrement."""
import ast
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]
tree=ast.parse((ROOT/'tools/verify_item_restore_controller_native.py').read_text(encoding='utf-8'))
source=next(n.args[0].value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='create_script')
source=source.replace('let maximum=100;','let maximum=100,selected=0,success=true;')
source=source.replace("replace(0x1c762,'void',['pointer','int'],'thiscall',()=>{});","replace(0x1c762,'void',['pointer','int'],'thiscall',action=>{if(success)action.add(28).writeU32(1);});\n replace(0x79a01,'void',['uint'],'mscdecl',()=>{});")
source=source.replace("'thiscall',()=>0);","'thiscall',()=>selected);")
start=source.index(' const rows=[];')
end=source.index(' return rows;',start)
source=source[:start]+'''
 const dispatch=new NativeFunction(b.add(0x1dc43),'uint',['pointer','uint8','uint8','int','int'],'thiscall');
 const rows=[];maximum=100;
 for(const category of [63,64])for(const stock of [0,1,2])for(const free of [0,1])for(const target of [0,255])for(const ok of [false,true]){
  selected=target;success=ok;
  actor.writeByteArray(new Uint8Array(36));actor.writeU32(0);actor.add(16).writeU32(50);actor.add(20).writeU32(50);
  const itemId=87,itemRecord=b.add(0xa1140+itemId*25);itemRecord.writeByteArray(new Uint8Array(25));itemRecord.add(17).writeU8(category);itemRecord.add(21).writeU8(30);
  b.add(0xb0770+0x26b).writeU8(stock);action.writeByteArray(new Uint8Array(0x40));
  const returned=dispatch(action,itemId,0,1,free);
  rows.push({category,stock,free,target,success:ok,returned,hp:actor.add(16).readU32(),mp:actor.add(20).readU32(),finalStock:b.add(0xb0770+0x26b).readU8()});
 }
''' +source[end:]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid);script=session.create_script(source);script.load();rows=script.exports_sync.capture()
    for row in rows:
        accepted=row['target']!=255
        completed=accepted and row['success']
        expected_stock=max(0,row['stock']-1) if completed and not row['free'] else row['stock']
        row['match']=row['returned']==int(completed) and row['finalStock']==expected_stock and row['hp']==(80 if accepted and row['category']==63 else 50) and row['mp']==(80 if accepted and row['category']==64 else 50)
    result=dict(total=len(rows),passed=sum(row['match'] for row in rows),rows=rows,scope='original 0x41DC43 restoration and stock decrement; selection and presentation-success controlled; not real animation cancellation semantics')
    text=json.dumps(result,indent=2)+'\n'
    (ROOT/'analysis/native-manual-item-dispatch-inventory.json').write_text(text,encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-manual-item-dispatch-inventory.json').write_text(text,encoding='utf-8')
    print(f'Native manual item dispatch inventory: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(row for row in rows if not row['match']))
finally:
    device.kill(pid)
    if session:session.detach()
