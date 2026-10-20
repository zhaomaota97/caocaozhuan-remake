"""Validate opcode 81 actor restoration, suppressing map/minimap UI callbacks."""
import itertools
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def main():
    cases=[dict(state=s,health=h,flags=f,status=t,resource=r) for s,h,f,t,r in
           itertools.product((0,1,2,3),(0,1,99,100),(0,2,255),(0,30,255),(0,50))]
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
  const b=Process.mainModule.base,keep=[];
  for(const rva of [0x53b13,0x4a88a]){
    const cb=new NativeCallback(()=>{},'void',['pointer'],'fastcall');keep.push(cb);Interceptor.replace(b.add(rva),cb);
  }
  Interceptor.flush();
  const unit=b.add(0xa1b68);unit.writeByteArray(new Uint8Array(72));unit.add(28).writeU32(100);
  for(const off of [0x2e,0x31,0x34])unit.add(off).writeU8(255);
  const table=b.add(0xb2c50),obj=Memory.alloc(0x2040),code=Memory.alloc(2);code.writeU16(81);
  const dispatch=new NativeFunction(b.add(0x109ef),'uint',['pointer'],'fastcall');
  return cases.map(c=>{
    const before=new Uint8Array(115*36).fill(165);
    for(let i=0;i<115;i++){
      const off=i*36;before.fill(0,off,off+4);before[off+12]=c.state;before[off+13]=c.flags;
      before[off+30]=c.status;
      for(let j=0;j<4;j++){before[off+16+j]=(c.health>>>(j*8))&255;before[off+20+j]=(c.resource>>>(j*8))&255;}
    }
    table.writeByteArray(before);obj.writeByteArray(new Uint8Array(0x2040));obj.add(12).writePointer(code);
    const status=dispatch(obj)&255,after=new Uint8Array(table.readByteArray(115*36));
    if(c.state===2)for(let i=0;i<115;i++){
      const off=i*36;before[off+13]&=~6;before[off+30]&=~30;
      before[off+16]=100;before[off+17]=before[off+18]=before[off+19]=0;
    }
    return {status,consumed:obj.add(12).readPointer().sub(code).toInt32(),
      actor_bytes_match:after.every((v,i)=>v===before[i])};
  });
}};
''')
        script.load();actual=script.exports_sync.verify(cases)
        rows=[dict(**c,actual=a,match=a['status']==1 and a['consumed']==2 and a['actor_bytes_match'])
              for c,a in zip(cases,actual)]
        (ROOT/'analysis/native-eex-restore-units-validation.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Native EEX restore units: {sum(r["match"] for r in rows)}/{len(rows)} contexts')
        if len(rows)!=288 or not all(r['match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
