"""Verify opcode 69 common-state writes and sentinel/truncation behavior."""
import itertools
import json
import struct
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def main():
    tags=[38,38,4,62,50,2,50,2,71,34];cases=[]
    for enabled,adjustment,unit,(mode,option) in itertools.product(
            (0,1,2,65535),(0,50,51,100,255,256,65535),(0,511,65535),
            ((65535,65535),(0,0),(2,2))):
        other=65535 if unit==0 else 0
        values=[enabled,65535,0x12345678,adjustment,0,unit,0,other,mode,option]
        raw=struct.pack('<H',69)+b''.join(struct.pack('<HI' if tag==4 else '<HH',tag,value) for tag,value in zip(tags,values))
        adjustment=0 if adjustment==65535 else adjustment
        expected=[int(enabled!=0),255,120,(adjustment if adjustment<51 else 50-adjustment)&255,
                  int(unit!=65535),unit,int(other!=65535),other,
                  0 if mode==65535 else mode,1 if option==65535 else option]
        cases.append(dict(values=values,bytes=list(raw),expected=expected))
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
  const b=Process.mainModule.base,obj=Memory.alloc(0x2040);
  const dispatch=new NativeFunction(b.add(0x109ef),'uint',['pointer'],'fastcall');
  return cases.map(c=>{
    const input=Memory.alloc(c.bytes.length);input.writeByteArray(c.bytes);
    obj.writeByteArray(new Uint8Array(0x2040));obj.add(12).writePointer(input);
    const status=dispatch(obj)&255;
    return {status,consumed:obj.add(12).readPointer().sub(input).toInt32(),fields:[
      b.add(0x94fd0).readU16(),b.add(0x96c9f).readU8(),b.add(0x92f90+0x3d0e).readU8(),
      b.add(0x96e23).readU8(),b.add(0x96c94).readU16(),b.add(0x96c96).readU16(),
      b.add(0x96c98).readU16(),b.add(0x96c9a).readU16(),b.add(0x96e21).readU8(),b.add(0x96e22).readU8()]};
  });
}};
''')
        script.load();native=script.exports_sync.verify(cases);rows=[]
        for case,actual in zip(cases,native):
            rows.append(dict(values=case['values'],expected=case['expected'],actual=actual,
                match=actual['status']==1 and actual['consumed']==len(case['bytes']) and actual['fields']==case['expected']))
        (ROOT/'analysis/native-eex-common-config-validation.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Native EEX common config: {sum(r["match"] for r in rows)}/{len(rows)}')
        if len(rows)!=252 or not all(r['match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
