"""Execute original actor renderer flag/HP gate with tile source and drawing controlled."""
import json
from pathlib import Path
import frida
from export_map_layouts import entries
ROOT=Path(__file__).resolve().parents[1]
palette=[value>>4 for value in dict(entries(ROOT/'Spalet.e5'))[31].ljust(768,b'\0')]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(palette){
 const b=Process.mainModule.base,keep=[],source=Memory.alloc(2304),actor=b.add(0xb2c50);let output=[];
 source.writeByteArray(Array.from({length:2304},(_,i)=>i&255));
 function replace(rva,ret,args,fn){const cb=new NativeCallback(fn,ret,args,'mscdecl');keep.push(cb);Interceptor.replace(b.add(rva),cb);}
 replace(0x3e572,'pointer',['int'],()=>source);
 replace(0x5137c,'void',['pointer','pointer','uint','uint','uint','pointer'],(_x,_y,_w,_h,_slot,p)=>{output=Array.from(new Uint8Array(p.readByteArray(2304)));});Interceptor.flush();
 b.add(0x97770).writeByteArray(palette);
 new NativeFunction(b.add(0x2fcc6),'void',['pointer'],'mscdecl')(b.add(0x97770));
 const dark=new NativeFunction(b.add(0x30480),'void',['pointer','int','int','uint8'],'mscdecl'),reference=Memory.alloc(256);reference.writeByteArray(Array.from({length:256},(_,i)=>i));dark(reference,256,1,4);
 const darkened=Array.from(new Uint8Array(reference.readByteArray(256)));
 const draw=new NativeFunction(b.add(0x3eb1f),'void',['pointer','pointer','int'],'mscdecl'),rows=[];
 for(let flags=0;flags<256;flags++)for(const hp of [0,1]){
  actor.writeByteArray(new Uint8Array(36));actor.add(13).writeU8(flags);actor.add(16).writeU32(hp);output=[];draw(ptr(0),ptr(0),0);
  if(output.length!==2304)throw new Error('Missing native draw output');
  const expected=(flags&6)===6&&hp!==0?darkened:Array.from({length:256},(_,i)=>i);
  rows.push({flags,hp,darkened:(flags&6)===6&&hp!==0,match:output.every((value,index)=>value===expected[index&255])});
 }
 return {rows,darkened};
}};
''');script.load();result=script.exports_sync.capture(palette)
    result.update(total=len(result['rows']),passed=sum(r['match'] for r in result['rows']),scope='original 0x43EB1F renderer, flags/HP getters, 0x430480 and lookup active; source tile and final drawing controlled; status flags zero, not status overlay/icon coverage')
    text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/native-acted-render-gate.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-acted-render-gate.json').write_text(text,encoding='utf-8')
    print(f'Native acted renderer gate: {result["passed"]}/{result["total"]}; 1179648 drawn pixels checked')
    if result['passed']!=result['total']:raise RuntimeError(next(r for r in result['rows'] if not r['match']))
finally:
    device.kill(pid)
    if session:session.detach()
