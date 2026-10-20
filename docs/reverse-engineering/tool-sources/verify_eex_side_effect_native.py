#!/usr/bin/env python3
"""Native synthetic checks for EEX handlers whose side effects are self-contained."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device(); lab=ROOT/'analysis/runtime-game'; pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab)); session=None
try:
 session=device.attach(pid)
 script=session.create_script('''
rpc.exports={verify(){
 const b=Process.mainModule.base;
 const clearPending=new NativeFunction(b.add(0x15c46),'uint',[]);
 const clearRuntime=new NativeFunction(b.add(0x16dfa),'uint',[]);
 const flag=b.add(0xae4c0); const runtime=b.add(0xb3d10); let a=[];
 flag.writeU8(1); a.push({case:'set',before:flag.readU8(),ret:clearPending(),after:flag.readU8()});
 flag.writeU8(0); a.push({case:'clear',before:flag.readU8(),ret:clearPending(),after:flag.readU8()});
 runtime.writeU8(0x7a); a.push({case:'runtime-default',before:runtime.readU8(),ret:clearRuntime(),after:runtime.readU8()});
 b.add(0xac63c).writeU8(3); runtime.writeU8(0x7a); a.push({case:'runtime-mode-3',before:runtime.readU8(),ret:clearRuntime(),after:runtime.readU8()});
 return a;
}};
'''); script.load(); result=script.exports_sync.verify()
 out={'opcode':7,'handler':'0x415c46','opcode_106_handler':'0x416dfa','cases':result,'passed':result[0]['ret']==1 and result[0]['after']==0 and result[1]['ret']==0 and result[1]['after']==0 and result[2]['ret']==1 and result[2]['after']==0x7a and result[3]['ret']==1 and result[3]['after']==0}
 (ROOT/'analysis/native-eex-side-effect-validation.json').write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out,indent=2))
 if not out['passed']: raise SystemExit(1)
finally:
 device.kill(pid)
 if session:
  try: session.detach()
  except frida.InvalidOperationError: pass
