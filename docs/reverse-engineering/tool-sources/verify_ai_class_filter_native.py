"""Call the original class-to-type-to-AI-filter chain without starting UI."""
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device()
pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'))
session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(){
 const b=Process.mainModule.base,actor=Memory.alloc(36),unit=b.add(0xa1b68);
 actor.writeByteArray(new Uint8Array(36));actor.writeU32(0);
 const previous=unit.add(43).readU8();
 const type=new NativeFunction(b.add(0x77d0),'uint',['pointer'],'fastcall');
 const filter=new NativeFunction(b.add(0x3ffed),'uint',['pointer'],'fastcall');
 const rows=[];
 try{for(let classId=0;classId<256;classId++){
  unit.add(43).writeU8(classId);rows.push({classId,type:type(unit),filtered:filter(actor)!==0});
 }}finally{unit.add(43).writeU8(previous);}
 return rows;
}};
''')
    script.load()
    rows=script.exports_sync.capture()
    for row in rows:
        c=row['classId'];kind=c//3 if c<39 else c-26 if c<53 else 27
        row['match']=row['type']==kind and row['filtered']==(kind in (8,9,10,11,18,19,20))
    result=dict(passed=sum(r['match'] for r in rows),total=len(rows),rows=rows,scope='native 0x43FFED -> 0x43B470 -> 0x4077D0; unit index zero; all byte values include invalid classes; no full battle scoring')
    text=json.dumps(result,indent=2)+'\n'
    (ROOT/'analysis/native-ai-class-filter.json').write_text(text,encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-ai-class-filter.json').write_text(text,encoding='utf-8')
    print(f'Native AI class filter: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(r for r in rows if not r['match']))
finally:
    device.kill(pid)
    if session:session.detach()
