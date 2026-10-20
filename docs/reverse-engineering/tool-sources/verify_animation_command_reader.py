"""Verify native animation opcode lengths and pointer advancement for all bytes."""
import json
from pathlib import Path
import frida
import pefile
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base,read=new NativeFunction(b.add(0x27f04),'uint',['pointer','pointer'],'mscdecl'),next=new NativeFunction(b.add(0x27f2e),'pointer',['pointer'],'mscdecl');
 const input=Memory.alloc(512),size=Memory.alloc(4),rows=[];
 for(let opcode=0;opcode<256;opcode++){
  input.writeU8(opcode);size.writeU32(0xa5a5a5a5);const result=read(input,size),advanced=next(input).sub(input).toInt32();
  rows.push({opcode,returnedByte:result&255,length:size.readU16(),upperWord:size.add(2).readU16(),advanced});
 }
 return rows;
}};''');script.load();rows=script.exports_sync.verify()
 pe=pefile.PE(str(ROOT/'Ekd5.exe'));lengths=pe.get_data(0x8b9d8,256)
 for row in rows:
  row['match']=(row['returnedByte']==row['opcode'] and row['length']==lengths[row['opcode']] and row['advanced']==lengths[row['opcode']] and row['upperWord']==0xa5a5)
 out={'scope':'Original 0x427F04 and 0x427F2E; no replacements; lengths cross-checked against PE bytes','rows':rows,'passed':len(rows)==256 and all(row['match'] for row in rows)}
 (ROOT/'analysis/native-animation-command-reader.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print(f"Native animation opcode length and pointer advance: {sum(row['match'] for row in rows)}/256")
 if not out['passed']:raise SystemExit(1)
finally:
 device.kill(pid)
 if session:session.detach()
