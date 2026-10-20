"""Validate EEX unit-attribute and turn comparisons, including native sentinel behavior."""
import json
import struct
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def parameter(tag,value):return struct.pack('<HI' if tag==4 else '<HH',tag,value)


def main():
    values=[37,41,53,67,79,0x12345678,91];cases=[]
    for channel,value in enumerate(values):
        for operator in (0,1,2,99):
            for threshold in (0,value-1,value,value+1,0x80000000,0xffffffff):
                expected=5 if threshold==0x80000000 else int(value>=threshold if operator==0 else value<threshold if operator==1 else value==threshold)
                raw=struct.pack('<H',54)+parameter(2,0)+parameter(35,channel)+parameter(4,threshold)+parameter(36,operator)
                cases.append(dict(opcode=54,channel=channel,operator=operator,threshold=threshold,expected=expected,bytes=list(raw)))
    for turn in (0,1,127,128,254,255):
        for operator in (0,1,2,99):
            for threshold in (0,1,2,128,255,256,0x80000000,0xffffffff):
                signed=threshold if threshold<0x80000000 else threshold-0x100000000
                expected=5 if threshold==0x80000000 else int(turn+1>=signed if operator==0 else turn+1<signed if operator==1 else turn+1==threshold)
                raw=struct.pack('<H',63)+parameter(4,threshold)+parameter(36,operator)
                cases.append(dict(opcode=63,turn=turn,operator=operator,threshold=threshold,expected=expected,bytes=list(raw)))
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(values,cases){
  const b=Process.mainModule.base,unit=b.add(0xa1b68),obj=Memory.alloc(0x2040);
  unit.writeByteArray(new Uint8Array(72));
  for(let i=0;i<5;i++)unit.add(21+i).writeU8(values[i]);
  unit.add(28).writeU32(values[5]);unit.add(32).writeU8(values[6]);
  const dispatch=new NativeFunction(b.add(0x109ef),'uint',['pointer'],'fastcall');
  return cases.map(c=>{
    const data=Memory.alloc(c.bytes.length);data.writeByteArray(c.bytes);
    obj.writeByteArray(new Uint8Array(0x2040));obj.add(12).writePointer(data);
    if(c.opcode===63)b.add(0xb3d0a).writeU8(c.turn);
    const status=dispatch(obj)&255;
    return {status,consumed:obj.add(12).readPointer().sub(data).toInt32()};
  });
}};
''')
        script.load();native=script.exports_sync.verify(values,cases);rows=[]
        for case,actual in zip(cases,native):
            # Sentinel failures stop before reading the final comparison-mode argument.
            length=(16 if case['opcode']==54 else 8) if case['threshold']==0x80000000 else len(case['bytes'])
            row={k:v for k,v in case.items() if k!='bytes'}
            row.update(actual=actual,expected_consumed=length,
                       match=actual['status']==case['expected'] and actual['consumed']==length)
            rows.append(row)
        (ROOT/'analysis/native-eex-numeric-predicates-validation.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Native EEX numeric predicates: {sum(r["match"] for r in rows)}/{len(rows)}')
        if len(rows)!=360 or not all(r['match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
