"""Probe original manual-item eligibility with real item categories and silent UI."""
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(bytes){
 const b=Process.mainModule.base,p=Memory.alloc(bytes.length);p.writeByteArray(bytes);
 const load=new NativeFunction(b.add(0xc537),'pointer',['pointer','pointer'],'thiscall');
 const check=new NativeFunction(b.add(0x1c4e9),'uint',['uint','uint','int'],'mscdecl');
 const silent=new NativeCallback(()=>{},'void',['int'],'mscdecl');Interceptor.replace(b.add(0x2f699),silent);Interceptor.flush();
 const actor=b.add(0xb2c50),unit=b.add(0xa1b68);actor.writeByteArray(new Uint8Array(36));actor.writeU32(0);
 const rows=[];
 for(let id=0;id<104;id++){
  const item=b.add(0xa1140+id*25);load(item,p.add(id*25));const category=item.add(17).readU8();
  if(category<63||category>76)continue;
  for(const mode of [0,1])for(const status of [0,2,4,8,16,30,255])for(const classId of [0,1,2,3,37,38,39,52])for(const level of [1,14,15,29,30,49,50]){
   actor.add(30).writeU8(status);unit.add(43).writeU8(classId);unit.add(44).writeU8(level);
   rows.push({id,category,mode,status,classId,level,eligible:check(id,0,mode)!==0});
  }
 }
 return rows;
}};
''');script.load()
    rows=script.exports_sync.capture(list(dict(entries(ROOT/'Data.e5'))[1]))
    for row in rows:
        c=row['category'];expected=True
        if row['mode'] and c in (65,66,67,68):expected=bool(row['status']&{65:8,66:16,67:2,68:4}[c])
        elif row['mode'] and c==69:expected=row['status']!=0
        elif c==75:expected=row['level']<50
        elif c==76:expected=row['classId']<39 and row['classId']%3!=2 and row['level']>=(row['classId']%3+1)*15
        row['match']=row['eligible']==expected
    result=dict(total=len(rows),passed=sum(row['match'] for row in rows),rows=rows,scope='native 0x41C4E9 and live getters; error-notification callback suppressed; no item mutation or inventory usage')
    text=json.dumps(result,indent=2)+'\n'
    (ROOT/'analysis/native-manual-item-eligibility.json').write_text(text,encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-manual-item-eligibility.json').write_text(text,encoding='utf-8')
    print(f'Native manual-item eligibility: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(row for row in rows if not row['match']))
finally:
    device.kill(pid)
    if session:session.detach()
