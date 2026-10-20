"""Execute the exact S_00 marked positioning block through the native interpreter."""
import json
import struct
from pathlib import Path
import frida
from export_eex_bodies import encode_block

ROOT=Path(__file__).resolve().parents[1]


def main():
    branches=json.loads((ROOT/'analysis/eex-bodies/S_00.json').read_text(encoding='utf-8'))
    block=next(n for n in branches[0]['nodes'] if n['opcode']==1 and n['condition']['offset']==5655)
    body=encode_block(dict(nodes=[block,dict(opcode=0)]))
    predicate=struct.pack('<HH',2,5)+b'\0'+b'\0\0'
    payload=predicate+struct.pack('<H',len(body))+body
    file=b'EEX\0\1\2\0\0\0\0'+struct.pack('<I',14)+struct.pack('<HH',1,len(payload))+payload
    snapshot=next(r['state_after'] for r in json.loads((ROOT/'analysis/native-s00-unit-setup-replay.json').read_text())['rows'] if r['opcode']==71)
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(bytes,snapshot){
 const b=Process.mainModule.base,input=Memory.alloc(bytes.length),obj=Memory.alloc(0x2040);
 input.writeByteArray(bytes);obj.writeByteArray(new Uint8Array(0x2040));
 obj.writePointer(b.add(0x86610));obj.add(16).writeU16(65535);obj.add(20).writeS32(-1);
 obj.add(32).writePointer(input);obj.add(40).writeU32(1);obj.add(48).writeU32(10);
 b.add(0x92F90).writeByteArray(snapshot);const visits=[];
 Interceptor.attach(b.add(0x15E31),{onEnter(){visits.push(1);}});
 const select=new NativeFunction(b.add(0x100A1),'uint',['pointer'],'fastcall');
 const execute=new NativeFunction(b.add(0x1084E),'int',['pointer','int','int'],'thiscall');
 const selected=select(obj),result=execute(obj,1,0);
 const r=b.add(0x92F90+0x2044);
 return {selected,result,position:[r.add(4).readU8(),r.add(5).readU8()],flags:r.add(8).readU32(),positionHandlers:visits.length};
}};
''');script.load();actual=script.exports_sync.verify(list(file),snapshot)
        expected=dict(selected=1,result=4,position=[7,0],flags=12,positionHandlers=15)
        report=dict(source='S_00 segment0 branch0, nested condition offset5655',
                    expected=expected,actual=actual,passed=expected==actual,
                    scope='exact marked positioning block re-encoded inside a minimal EEX container; native selector/interpreter/condition/setters; opcode71 snapshot supplied; not full S_00 entry execution')
        (ROOT/'analysis/native-s00-position-block-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(report)
        if not report['passed']:raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
