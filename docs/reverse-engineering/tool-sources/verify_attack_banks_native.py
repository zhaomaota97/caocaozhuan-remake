"""Compare original attack-bank selection and mirroring against decoded art."""
import hashlib
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]


def main():
    resources=dict(entries(ROOT/'Unit_atk.e5'))
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(resources){
  const b=Process.mainModule.base,keep=[];let index=0;
  function replace(rva,ret,args,abi,fn){
    const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);
    Interceptor.replace(b.add(rva),cb);
  }
  replace(0x32b0,'pointer',['pointer'],'fastcall',p=>p);
  replace(0x32d0,'void',['pointer'],'fastcall',()=>{});
  replace(0x1fb35,'uint8',['pointer','pointer'],'thiscall',()=>1);
  replace(0x192c5,'uint',['pointer'],'fastcall',()=>1);
  replace(0x3fc48,'uint',['pointer'],'fastcall',()=>index);
  replace(0x1fc89,'uint',['pointer','int','pointer'],'thiscall',(_obj,i,out)=>{
    out.writeByteArray(resources[i]);return resources[i].length;
  });
  Interceptor.flush();
  const scratch=Memory.alloc(0x14000);scratch.writeByteArray(new Uint8Array(0x14000));
  const view=b.add(0xae4c8);view.add(4).writeU32(0x14000);
  view.add(12).writePointer(scratch);view.add(16).writeU8(1);
  const actor=Memory.alloc(0x24), action=Memory.alloc(16);
  actor.writeByteArray(new Uint8Array(0x24));action.add(12).writePointer(actor);
  const select=new NativeFunction(b.add(0x3b8f),'void',['pointer'],'fastcall');
  const rows=[];
  for(index=0;index<resources.length;index++)for(let direction=0;direction<4;direction++){
    actor.add(15).writeU8(direction);select(action);
    rows.push({index,direction,sha256:Checksum.compute('sha256',scratch.readByteArray(16384))});
  }
  return rows;
}};
''')
        script.load()
        rows=script.exports_sync.verify([list(resources[i]) for i in range(len(resources))])
        for row in rows:
            bank=[1,2,0,2][row['direction']]
            image=resources[row['index']][bank*16384:(bank+1)*16384]
            if row['direction']==1:
                image=b''.join(image[i:i+64][::-1] for i in range(0,len(image),64))
            row['expected_sha256']=hashlib.sha256(image).hexdigest()
            row['match']=row['sha256']==row['expected_sha256']
        (ROOT/'analysis/native-attack-bank-validation.json').write_text(
            json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Native attack banks: {sum(r["match"] for r in rows)}/{len(rows)}')
        if len(rows)!=604 or not all(r['match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
