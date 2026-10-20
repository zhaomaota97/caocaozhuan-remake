"""Verify native opcode-52 effect-table lookup/reset with a controlled entry."""
import json
from pathlib import Path
import frida
import pefile
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();lab=ROOT/'analysis/runtime-game';pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base,keep=[];let commits=0;
 const commit=new NativeCallback(()=>{commits++;return 0;},'uint',[],'mscdecl');keep.push(commit);Interceptor.replace(b.add(0x28b05),commit);Interceptor.flush();
 const dispatch=new NativeFunction(b.add(0x28b87),'uint',['int16','int16','int16'],'mscdecl');
 const table=b.add(0x9cf68),rows=[];
 for(let index=0;index<128;index++)for(const second of [-1,0,1,18])for(const third of [-1,0,3,32767,-32768]){
  table.writeByteArray(new Uint8Array(128*64));
  for(let i=0;i<128;i++){const p=table.add(i*64);p.add(0x1a).writeU16(0x6a6a);p.add(0x2c).writeU16(0x2345);p.add(0x2e).writeU16(0x3456);}
  const entry=table.add(index*64);entry.add(0x28).writeU16(0x8000);entry.add(0x3a).writeU16(0x1234);entry.add(0x34).writeU32(0);entry.add(0x2a).writeU16(0x6b6b);
  if(index>0){const inactive=table.add((index-1)*64);inactive.add(0x28).writeU16(1);inactive.add(0x3a).writeU16(0x1234);}
  commits=0;const ret=dispatch(0x1234,second,third);
  const untouched=Array.from({length:128},(_,i)=>i).filter(i=>i!==index).every(i=>table.add(i*64+0x1a).readU16()===0x6a6a&&table.add(i*64+0x2e).readU16()===0x3456);
  rows.push({index,secondInput:second,third,ret,commits,untouched,flags:entry.add(0x28).readU16(),reset:entry.add(0x1a).readU16(),second:entry.add(0x2c).readU16(),resourceRva:entry.add(0x34).readPointer().isNull()?null:entry.add(0x34).readPointer().sub(b).toInt32(),resourceKind:entry.add(0x2a).readU16(),thirdField:entry.add(0x2e).readU16(),key:entry.add(0x3a).readU16()});
 }
 commits=0;const missing=dispatch(0x7fff,-1,-1);return {rows,missing,missingCommits:commits};
}};''');script.load();result=script.exports_sync.verify()
 pe=pefile.PE(str(lab/'Ekd5.exe'))
 definitions=pe.get_data(0x8b920,19*9)
 for row in result['rows']:
  second=row['secondInput']
  row['match']=(row['ret']==0 and row['flags']==0x8000 and row['reset']==0 and row['second']==(0x2345 if second==-1 else second)
                and row['resourceRva']==(None if second==-1 else 0x8b920+second*9)
                and row['resourceKind']==(0x6b6b if second==-1 else definitions[second*9+1])
                and row['thirdField']==(0x3456 if row['third']==-1 else row['third']&65535)
                and row['key']==0x1234 and row['untouched'] and row['commits']==1)
 out={'result':result,'resourceDefinitions':[definitions[i*9:(i+1)*9].hex() for i in range(19)],'passed':len(result['rows'])==2560 and all(x['match'] for x in result['rows']) and result['missing']==0xffffffff and result['missingCommits']==0}
 (ROOT/'analysis/native-eex-effect-dispatch-validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(f"Native effect dispatch/resource selection: {sum(row['match'] for row in result['rows'])}/2560; missing key commits={result['missingCommits']}")
 if not out['passed']:raise SystemExit(1)
finally:
 device.kill(pid)
 if session:
  try:session.detach()
  except frida.InvalidOperationError:pass
