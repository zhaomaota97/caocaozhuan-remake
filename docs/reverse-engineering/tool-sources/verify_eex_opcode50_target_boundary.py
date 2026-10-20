"""Verify safe native opcode-50 target branches without rendering."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();lab=ROOT/'analysis/runtime-game';pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base,run=new NativeFunction(b.add(0x29159),'uint',['int16','int16','int16','uint16'],'mscdecl'),table=b.add(0x9cf68),rows=[];
 const entry=table.add(3*0x40);entry.writeByteArray(new Uint8Array(0x40));entry.add(0x28).writeU16(0x8000);entry.add(0x3a).writeU16(0x3456);entry.add(0x30).writeU16(3);
 rows.push({case:'missing',ret:run(0x7fff,0,0,0)});rows.push({case:'non-type4',ret:run(0x3456,0,0,0)});return rows;
}};''');script.load();result=script.exports_sync.verify()
 out={'rows':result,'passed':all(x['ret']==0xffff for x in result)}
 (ROOT/'analysis/native-eex-opcode50-target-validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
 if not out['passed']:raise SystemExit(1)
finally:
 device.kill(pid)
 if session:
  try:session.detach()
  except frida.InvalidOperationError:pass
