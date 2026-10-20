"""Capture original unit terrain clipping with actual raw MARK masks."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1];mark=(ROOT/'Mark.e5').read_bytes();cases=[]
for size in [48,64]:
    for terrain,offset in [(9,0x4bc0 if size==64 else 0x27c0),(10,0x4bc0 if size==64 else 0x27c0),(2,0x5bc0 if size==64 else 0x30c0),(1,0x6bc0 if size==64 else 0x39c0),(7,0x7bc0 if size==64 else 0x42c0)]:
        cases.append(dict(size=size,terrain=terrain,offset=offset,mask=list(mark[offset:offset+size*size])))
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(cases){
 const b=Process.mainModule.base,apply=new NativeFunction(b.add(0x30a07),'void',['pointer','pointer','uint','uint','int8'],'mscdecl');
 return cases.map(row=>{const count=row.size*row.size,src=Memory.alloc(count),mask=Memory.alloc(count);src.writeByteArray(Array.from({length:count},(_,i)=>i&255));mask.writeByteArray(row.mask);apply(src,mask,row.size,row.size,0);return {...row,pixels:Array.from(new Uint8Array(src.readByteArray(count)))};});
}};
''');script.load();rows=script.exports_sync.capture(cases)
    for row in rows:row['match']=row['pixels']==[0 if mask else index&255 for index,mask in enumerate(row['mask'])]
    result=dict(total=len(rows),passed=sum(row['match'] for row in rows),rows=rows,scope='original 0x430A07 with actual MARK masks; terrain-to-offset mapping static 0x45137C; final terrain getter and full draw not executed')
    text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/native-unit-terrain-mask.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-unit-terrain-mask.json').write_text(text,encoding='utf-8')
    mapping=dict(source='Mark.e5',rows=[dict(size=row['size'],terrain=row['terrain'],offset=row['offset'],blocked=[bool(value) for value in row['mask']]) for row in rows])
    (ROOT.parent/'caocaozhuan-remake/data/mappings/unit-terrain-masks.json').write_text(json.dumps(mapping,indent=2)+'\n',encoding='utf-8')
    print(f'Native unit terrain masks: {result["passed"]}/{result["total"]}, {sum(len(r["pixels"]) for r in rows)} pixels')
    if result['passed']!=result['total']:raise RuntimeError('Native mask mismatch')
finally:
    device.kill(pid)
    if session:session.detach()
