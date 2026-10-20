"""Validate script-to-animation argument routing without rendering/game movement."""
import itertools
import json
import struct
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def stream(opcode,tags,values):
    return struct.pack('<H',opcode)+b''.join(struct.pack('<HH',t,v) for t,v in zip(tags,values))


def main():
    cases=[]
    for uid,target,style,toggles in itertools.product((0,511,65535),(0,65535),(2,258),itertools.product((0,1,2,65535),repeat=3)):
        values=[uid,target,style,*toggles]
        flags=[int((default if value==65535 else value)==1) for value,default in zip(toggles,(0,1,1))]
        raw=stream(79,[2,2,43,38,38,38],values)
        cases.append(dict(opcode=79,values=values,bytes=list(raw),calls=[['move',uid,target,style&255,*flags]],status=1,consumed=len(raw)))
    for uid,action,toggles in itertools.product((0,511,65535),(0,11,256,65535),itertools.product((0,1,2,65535),repeat=2)):
        values=[uid,action,*toggles]
        flags=[int(value in (1,65535)) for value in toggles]
        raw=stream(80,[2,70,38,38],values)
        calls=[] if action==65535 else [['pose',uid,action&255,*flags]]
        cases.append(dict(opcode=80,values=values,bytes=list(raw),calls=calls,status=1,consumed=len(raw)))
    for opcode,tags in [(79,[2,2,43,38,38,38]),(80,[2,70,38,38])]:
        for index in range(len(tags)):
            bad=tags.copy();bad[index]=99
            raw=stream(opcode,bad,[0]*len(tags))
            cases.append(dict(opcode=opcode,bad_tag=index,bytes=list(raw),calls=[],status=5,consumed=2+index*4+2))
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
  const b=Process.mainModule.base;let calls=[];
  const move=new NativeCallback((uid,target,style,a,c,d)=>{calls.push(['move',uid,target,style,a,c,d]);},
    'void',['uint','int','uint8','int','int','int'],'mscdecl');
  const pose=new NativeCallback((uid,action,a,c)=>{calls.push(['pose',uid,action,a,c]);},
    'void',['uint','uint8','int','int'],'mscdecl');
  Interceptor.replace(b.add(0x57428),move);Interceptor.replace(b.add(0x5778f),pose);Interceptor.flush();
  const dispatch=new NativeFunction(b.add(0x109ef),'uint',['pointer'],'fastcall'),obj=Memory.alloc(0x2040);
  return cases.map(c=>{
    const input=Memory.alloc(c.bytes.length);input.writeByteArray(c.bytes);
    obj.writeByteArray(new Uint8Array(0x2040));obj.add(12).writePointer(input);calls=[];
    return {status:dispatch(obj)&255,consumed:obj.add(12).readPointer().sub(input).toInt32(),calls:calls.slice()};
  });
}};
''')
        script.load();native=script.exports_sync.verify(cases);failures=[]
        for case,actual in zip(cases,native):
            if any(actual[k]!=case[k] for k in ('status','consumed','calls')):
                failures.append(dict(**{k:v for k,v in case.items() if k!='bytes'},actual=actual))
        result=dict(cases=len(cases),matched=len(cases)-len(failures),failures=failures)
        (ROOT/'analysis/native-eex-animation-command-validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(f'Native EEX animation commands: {result["matched"]}/{len(cases)}')
        if len(cases)!=970 or failures:raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
