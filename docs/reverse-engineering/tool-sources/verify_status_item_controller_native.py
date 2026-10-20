"""Execute native status-item dispatcher for every input status byte."""
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(){
 const b=Process.mainModule.base,keep=[];let selected=0;
 function replace(rva,ret,args,abi,fn){const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);Interceptor.replace(b.add(rva),cb);}
 replace(0x1c762,'void',['pointer','int'],'thiscall',action=>action.add(28).writeU32(1));
 replace(0x5533d,'uint8',['pointer','uint8','int8','int8','uint8'],'thiscall',()=>selected);
 replace(0x79a01,'void',['uint'],'mscdecl',()=>{});Interceptor.flush();
 const actor=b.add(0xb2c50),item=b.add(0xa1140+92*25),action=Memory.alloc(0x40);
 const dispatch=new NativeFunction(b.add(0x1dc43),'uint',['pointer','uint8','uint8','int','int'],'thiscall');
 const rows=[];
 for(const category of [65,66,67,68,69])for(let status=0;status<256;status++)for(const target of [0,255]){
  selected=target;actor.writeByteArray(new Uint8Array(36));actor.add(30).writeU8(status);actor.add(13).writeU8(165);
  item.writeByteArray(new Uint8Array(25));item.add(17).writeU8(category);action.writeByteArray(new Uint8Array(0x40));
  const returned=dispatch(action,92,0,1,1);
  rows.push({category,status,target,returned,finalStatus:actor.add(30).readU8(),actorFlags:actor.add(13).readU8()});
 }
 return rows;
}};
''');script.load();rows=script.exports_sync.capture()
    masks={65:8,66:16,67:2,68:4,69:30}
    for row in rows:
        selected=row['target']!=255
        row['match']=row['finalStatus']==(row['status']&~masks[row['category']] if selected else row['status']) and row['returned']==int(selected) and row['actorFlags']==165
    result=dict(total=len(rows),passed=sum(row['match'] for row in rows),rows=rows,scope='native 0x41DC43 -> 0x41CF61 -> 0x418DA0; target and presentation-success controlled, free-use path; actor flags preservation checked')
    text=json.dumps(result,indent=2)+'\n'
    (ROOT/'analysis/native-status-item-controller.json').write_text(text,encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-status-item-controller.json').write_text(text,encoding='utf-8')
    print(f'Native status-item controller: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(row for row in rows if not row['match']))
finally:
    device.kill(pid)
    if session:session.detach()
