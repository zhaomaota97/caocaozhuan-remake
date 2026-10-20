"""Probe original palette wrapper's short-resource tail behavior."""
import json
from pathlib import Path
import frida
from export_map_layouts import entries
ROOT=Path(__file__).resolve().parents[1]
raw=dict(entries(ROOT/'Spalet.e5'))[31]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(bytes){
 const b=Process.mainModule.base,keep=[];function replace(rva,ret,args,abi,fn){const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);Interceptor.replace(b.add(rva),cb);}
 replace(0x32b0,'pointer',['pointer'],'fastcall',p=>p);
 replace(0x32d0,'void',['pointer'],'fastcall',()=>{});
 replace(0x7d1ca,'void',['int'],'mscdecl',()=>{});
 replace(0x1fb35,'uint8',['pointer','pointer'],'thiscall',()=>1);
 replace(0x1fc89,'uint',['pointer','int','pointer'],'thiscall',(_file,_index,dest)=>{dest.writeByteArray(bytes);return bytes.length;});
 replace(0x192c5,'uint',['pointer'],'fastcall',()=>1);
 replace(0x2fcc6,'void',['pointer'],'mscdecl',()=>{});Interceptor.flush();
 const load=new NativeFunction(b.add(0x1e050),'void',['uint','int8'],'mscdecl'),rows=[];
 for(const initial of [0,15,128,255]){
  b.add(0x97770).writeByteArray(new Uint8Array(768).fill(initial));load(31,1);
  rows.push({initial,palette:Array.from(new Uint8Array(b.add(0x97770).readByteArray(768)))});
 }
 return rows;
}};
''');script.load();rows=script.exports_sync.capture(list(raw))
    for row in rows:row['match']=row['palette']==[v>>4 for v in raw]+[row['initial']>>4]*(768-len(raw))
    result=dict(resourceBytes=len(raw),total=len(rows),passed=sum(r['match'] for r in rows),rows=rows,scope='original 0x41E050 conversion loop; resource read controlled to exact decoded bytes; file/UI/lookup leaves replaced; proves wrapper preservation, not actual live preceding palette')
    text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/native-short-palette-tail.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-short-palette-tail.json').write_text(text,encoding='utf-8')
    print(f'Native short palette tail: {result["passed"]}/{result["total"]}, resource {len(raw)} bytes')
    if result['passed']!=result['total']:raise RuntimeError('Palette mismatch')
finally:
    device.kill(pid)
    if session:session.detach()
