"""Verify self-contained low-frequency EEX opcode handlers."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();lab=ROOT/'analysis/runtime-game';pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base, rows=[];
 const clearTable=new NativeFunction(b.add(0x15ad7),'uint',['pointer'],'mscdecl');
 const fixed3=new NativeFunction(b.add(0x112df),'uint',[],'mscdecl');
 const fixed12=new NativeFunction(b.add(0x143a4),'uint',[],'mscdecl');
 const fixed13=new NativeFunction(b.add(0x143ae),'uint',[],'mscdecl');
 const fixed30=new NativeFunction(b.add(0x13ef1),'uint',[],'mscdecl');
 const consume=new NativeFunction(b.add(0x15c46),'uint',[],'mscdecl');
 const table=Memory.alloc(0x438);for(let i=0;i<256;i++)table.add(0x38+i*4).writeU32(0xa5a5a5a5);
 rows.push({opcode:10,before:table.add(0x38+4*0).readU32(),ret:clearTable(table),after:table.add(0x38+4*0).readU32(),last:table.add(0x38+4*255).readU32()});
 rows.push({opcode:3,ret:fixed3()});rows.push({opcode:12,ret:fixed12()});rows.push({opcode:13,ret:fixed13()});rows.push({opcode:30,ret:fixed30()});
 const flag=b.add(0xae4c0);flag.writeU8(1);rows.push({opcode:7,ret:consume(),after:flag.readU8()});
 return rows;
}};''');script.load();result=script.exports_sync.verify()
 out={'cases':result,'passed':result[0]['ret']==1 and result[0]['after']==0 and result[0]['last']==0 and result[1]['ret']==6 and result[2]['ret']==8 and result[3]['ret']==7 and result[4]['ret']==2 and result[5]['ret']==1 and result[5]['after']==0}
 (ROOT/'analysis/native-eex-low-frequency-validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
 if not out['passed']:raise SystemExit(1)
finally:
 device.kill(pid)
 if session:
  try:session.detach()
  except frida.InvalidOperationError:pass
