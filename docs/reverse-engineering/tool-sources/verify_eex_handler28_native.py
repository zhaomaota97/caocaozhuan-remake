#!/usr/bin/env python3
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]; device=frida.get_local_device(); lab=ROOT/'analysis/runtime-game'; pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab)); session=None
try:
 session=device.attach(pid)
 script=session.create_script('''
rpc.exports={verify(){
 const b=Process.mainModule.base;const h=new NativeFunction(b.add(0x13ebd),'uint',[]);const mode=b.add(0xac63c);let out=[];
 for(const v of [0,2]){mode.writeU8(v);try{out.push({mode:v,ret:h()});}catch(e){out.push({mode:v,error:String(e)});}}
 return out;
}};
'''); script.load(); out=script.exports_sync.verify(); print(json.dumps({'opcode':28,'handler':'0x413ebd','results':out},indent=2));
 (ROOT/'analysis/native-eex-handler28-validation.json').write_text(json.dumps({'opcode':28,'handler':'0x413ebd','results':out},indent=2),encoding='utf-8')
finally:
 device.kill(pid)
 if session:
  try: session.detach()
  except frida.InvalidOperationError: pass
