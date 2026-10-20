"""Validate opcode 70's twenty enemy setup records against original global writes."""
import hashlib
import itertools
import json
import struct
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]
TAGS=[2,38,4,4,43,62,69,7,2,4,4]


def main():
    cases=[]
    for base,adjustment in itertools.product((1,10,49,50),(0,1,50,51,100,65535)):
        raw=struct.pack('<H',70);expected=bytearray([165]*(20*64))
        for i in range(20):
            uid=65535 if i%3==0 else 100+i
            flag=65535 if i%3==0 else i%2
            pose=65535 if i%2 else 3
            ai=65535 if i==19 else i%7
            values=[uid,flag,i,19-i,i%4,adjustment,pose,ai,200+i,50+i,60+i]
            for tag,value in zip(TAGS,values):raw+=struct.pack('<HI' if tag==4 else '<HH',tag,value)
            if uid==65535:continue
            off=i*64;modifier=0 if adjustment==65535 else adjustment
            level=min(base+modifier,50) if modifier<51 else max(base-(modifier-50),1)
            struct.pack_into('<I',expected,off,uid);expected[off+4]=i;expected[off+5]=19-i
            struct.pack_into('<I',expected,off+8,2|(4 if flag else 0)|[32,8,64,16][i%4])
            expected[off+16]=2 if pose==65535 else pose;expected[off+17]=level
            ai=1 if ai==65535 else ai;expected[off+12]=ai
            if ai in (3,5):struct.pack_into('<H',expected,off+14,200+i)
            elif ai in (4,6):expected[off+14]=50+i;expected[off+15]=60+i
            expected[off+20:off+32]=bytes(12);expected[off+32]=expected[off+33]=1
        cases.append(dict(base=base,adjustment=adjustment,bytes=list(raw),
                          expected_hash=hashlib.sha256(expected).hexdigest()))
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
  const b=Process.mainModule.base,obj=Memory.alloc(0x2040),start=b.add(0x92f90+0x2044+15*64);
  const party=b.add(0x8b350);Memory.protect(party,20,'rw-');
  for(let i=0;i<4;i++)party.add(i*4).writeU32(i);party.add(16).writeU32(65535);
  const dispatch=new NativeFunction(b.add(0x109ef),'uint',['pointer'],'fastcall');
  return cases.map(c=>{
    for(let i=0;i<512;i++)b.add(0xa1b68+i*72+44).writeU8(c.base);
    b.add(0x96e23).writeU8(0);start.writeByteArray(new Uint8Array(20*64).fill(165));
    const input=Memory.alloc(c.bytes.length);input.writeByteArray(c.bytes);
    obj.writeByteArray(new Uint8Array(0x2040));obj.add(12).writePointer(input);
    const status=dispatch(obj)&255;
    return {status,consumed:obj.add(12).readPointer().sub(input).toInt32(),
      hash:Checksum.compute('sha256',start.readByteArray(20*64))};
  });
}};
''')
        script.load();native=script.exports_sync.verify(cases);rows=[]
        for case,actual in zip(cases,native):
            rows.append(dict(base=case['base'],adjustment=case['adjustment'],actual=actual,
                expected_hash=case['expected_hash'],match=actual['status']==1 and
                actual['consumed']==len(case['bytes']) and actual['hash']==case['expected_hash']))
        (ROOT/'analysis/native-eex-enemy-setup-validation.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Native enemy setup: {sum(r["match"] for r in rows)}/{len(rows)} contexts, 480 records')
        if len(rows)!=24 or not all(r['match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
