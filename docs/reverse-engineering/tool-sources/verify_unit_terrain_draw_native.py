"""Run full native tile drawing wrapper for the recovered terrain-mask branches."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1];mark=(ROOT/'Mark.e5').read_bytes()
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(mark){
 const b=Process.mainModule.base,keep=[],resource=Memory.alloc(mark.length),source=Memory.alloc(4096);resource.writeByteArray(mark);source.writeByteArray(Array.from({length:4096},(_,i)=>i&255));let terrain=0,output=[],offsets=[];
 const getTerrain=new NativeCallback(()=>terrain,'uint8',['pointer'],'mscdecl');keep.push(getTerrain);Interceptor.replace(b.add(0x35991),getTerrain);
 const getResource=new NativeCallback((_object,offset)=>{offsets.push(offset);return resource.add(offset);},'pointer',['pointer','uint','uint','uint'],'thiscall');keep.push(getResource);Interceptor.replace(b.add(0x7fa40),getResource);
 const finalDraw=new NativeCallback((_x,_y,w,h,p,_mode)=>{output=Array.from(new Uint8Array(p.readByteArray(w*h)));},'void',['pointer','pointer','uint','uint','pointer','uint'],'mscdecl');keep.push(finalDraw);Interceptor.replace(b.add(0x51913),finalDraw);Interceptor.flush();
 const draw=new NativeFunction(b.add(0x5137c),'void',['pointer','pointer','uint','uint','uint','pointer'],'mscdecl'),rows=[];
 for(const size of [48,64])for(const code of [0,1,2,7,9,10,255]){
  terrain=code;output=[];offsets=[];draw(ptr(0),ptr(0),size,size,0,source);rows.push({size,terrain:code,offsets,pixels:output});
 }
 return rows;
}};
''');script.load();rows=script.exports_sync.capture(list(mark))
    offsets={48:{1:0x39c0,2:0x30c0,7:0x42c0,9:0x27c0,10:0x27c0},64:{1:0x6bc0,2:0x5bc0,7:0x7bc0,9:0x4bc0,10:0x4bc0}}
    for row in rows:
        offset=offsets[row['size']].get(row['terrain']);count=row['size']**2
        expected=[index&255 if offset is None or mark[offset+index]==0 else 0 for index in range(count)]
        row['match']=row['pixels']==expected and row['offsets']==([] if offset is None else [offset])
    result=dict(total=len(rows),passed=sum(row['match'] for row in rows),rows=rows,scope='original 0x45137C terrain dispatch and mask helper; actual MARK data; terrain query, buffer accessor and final draw controlled; excludes special terrain13')
    text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/native-unit-terrain-draw.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-unit-terrain-draw.json').write_text(text,encoding='utf-8')
    print(f'Native unit terrain draw wrapper: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(row for row in rows if not row['match']))
finally:
    device.kill(pid)
    if session:session.detach()
