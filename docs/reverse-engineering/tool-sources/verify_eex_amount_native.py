"""Check opcode 58 amount updates, saturation, signed-add behavior, and sentinels."""
import itertools
import json
import struct
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def main():
    cases=[]
    for initial,mode,value in itertools.product((0,10,999998,999999),range(4),
                                               (0,1,999999,1000000,0xffffffff,0x80000000)):
        status=5 if mode==3 or value==0x80000000 else 1
        result=initial
        if status==1:
            if mode==0:result=min(value,999999)
            elif mode==2:result=max(initial-value,0)
            else:
                summed=(initial+value)&0xffffffff
                signed=summed if summed<0x80000000 else summed-0x100000000
                result=min(min(signed,999999)&0xffffffff,999999)
        raw=struct.pack('<HHHHHHI',58,40,0,52,mode,4,value)
        cases.append(dict(initial=initial,mode=mode,value=value,expected=result,
                          status=status,bytes=list(raw)))
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
  const b=Process.mainModule.base,common=b.add(0xb0770),obj=Memory.alloc(0x2040);
  const dispatch=new NativeFunction(b.add(0x109ef),'uint',['pointer'],'fastcall');
  return cases.map(c=>{
    common.writeByteArray(new Uint8Array(32).fill(165));common.add(12).writeU32(c.initial);
    const input=Memory.alloc(c.bytes.length);input.writeByteArray(c.bytes);
    obj.writeByteArray(new Uint8Array(0x2040));obj.add(12).writePointer(input);
    const status=dispatch(obj)&255,bytes=new Uint8Array(common.readByteArray(32));
    return {status,value:common.add(12).readU32(),consumed:obj.add(12).readPointer().sub(input).toInt32(),
      guard:bytes.every((v,i)=>i>=12&&i<16||v===165)};
  });
}};
''')
        script.load();native=script.exports_sync.verify(cases)
        rows=[dict(**{k:v for k,v in c.items() if k!='bytes'},actual=a,
                   match=a['status']==c['status'] and a['value']==c['expected'] and
                   a['consumed']==16 and a['guard']) for c,a in zip(cases,native)]
        (ROOT/'analysis/native-eex-amount-validation.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Native EEX amount updates: {sum(r["match"] for r in rows)}/{len(rows)}')
        if len(rows)!=96 or not all(r['match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
