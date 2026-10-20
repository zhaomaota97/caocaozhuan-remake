"""Validate opcode 65 unit counting on a constructed four-cell battle map."""
import itertools
import json
import struct
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def main():
    cases=[]
    for group,region,active,threshold,operator in itertools.product(
            [*range(7),65535],(0,1),range(16),range(6),(0,1,2,99)):
        count=0
        for slot in (range(2) if region else range(4)):
            if not active&(1<<slot):continue
            if group==slot or group==4 and slot<2 or group==5 and slot>=2 or group in (6,65535):count+=1
        expected=int(count>=threshold if operator==0 else count<threshold if operator==1 else count==threshold)
        raw=struct.pack('<H',65)
        for tag,value in [(3,group),(4,threshold),(36,operator),(63,region),
                          (4,0),(4,0),(4,1),(4,0)]:
            raw+=struct.pack('<HI' if tag==4 else '<HH',tag,value)
        cases.append(dict(group=group,region=region,active=active,threshold=threshold,
                          operator=operator,count=count,expected=expected,bytes=list(raw)))
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
  const b=Process.mainModule.base,map=Memory.alloc(0xc84),v=b.add(0xaeb38);
  map.writeByteArray(new Uint8Array(0xc84).fill(255));map.add(0xc80).writeByteArray([0,1,2,3]);
  v.add(4).writeU32(0xc84);v.add(12).writePointer(map);v.add(16).writeU8(1);
  b.add(0xb422c).writeU8(2);b.add(0xb422d).writeU8(2);
  b.add(0xb2c50).writeByteArray(new Uint8Array(115*36));
  const dispatch=new NativeFunction(b.add(0x109ef),'uint',['pointer'],'fastcall'),obj=Memory.alloc(0x2040);
  return cases.map(c=>{
    for(let i=0;i<4;i++){
      const actor=b.add(0xb2c50+i*36);actor.writeU32(i);
      actor.add(5).writeU8(i);actor.add(12).writeU8((c.active&(1<<i))?2:0);
    }
    const input=Memory.alloc(c.bytes.length);input.writeByteArray(c.bytes);
    obj.writeByteArray(new Uint8Array(0x2040));obj.add(12).writePointer(input);
    return {value:dispatch(obj)&255,consumed:obj.add(12).readPointer().sub(input).toInt32()};
  });
}};
''')
        script.load();native=script.exports_sync.verify(cases)
        failures=[]
        for case,actual in zip(cases,native):
            if actual['value']!=case['expected'] or actual['consumed']!=len(case['bytes']):
                failures.append(dict(**{k:v for k,v in case.items() if k!='bytes'},actual=actual))
        result=dict(cases=len(cases),matched=len(cases)-len(failures),failures=failures)
        (ROOT/'analysis/native-eex-unit-count-validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(f'Native EEX unit count: {result["matched"]}/{len(cases)}')
        if len(cases)!=6144 or failures:raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
