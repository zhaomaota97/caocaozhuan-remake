"""Execute S_00 Zhang Bao's actual opcode61 through the native inventory writer."""
import json
from pathlib import Path
import frida
from export_eex_bodies import encode_instruction
from export_map_layouts import entries
from export_story_readable import walk

ROOT=Path(__file__).resolve().parents[1]


def main():
    node=next(n for branch in json.loads((ROOT/'analysis/eex-bodies/S_00.json').read_text(encoding='utf-8'))
              for n,_ in walk(branch['nodes']) if n['offset']==14459)
    instruction=encode_instruction(node)
    if instruction!=(ROOT/'S_00.eex').read_bytes()[14459:14477]:raise ValueError('Drop instruction not byte-exact')
    items=dict(entries(ROOT/'Data.e5'))[1]
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(items,bytes){
 const b=Process.mainModule.base,keep=[],source=Memory.alloc(items.length),input=Memory.alloc(bytes.length);
 source.writeByteArray(items);input.writeByteArray(bytes);let discoveries=[],prompts=[];
 function replace(rva,ret,args,abi,fn){const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);Interceptor.replace(b.add(rva),cb);}
 replace(0x81100,'int',['pointer'],'mscdecl',()=>0);
 replace(0x2F699,'uint',['uint'],'mscdecl',(mode)=>{prompts.push(mode);return 0;});
 replace(0x1A1B0,'void',['uint','uint8'],'mscdecl',(index,value)=>discoveries.push({index,value}));
 Interceptor.flush();
 const load=new NativeFunction(b.add(0x0C537),'pointer',['pointer','pointer'],'thiscall');
 for(let i=0;i<104;i++)load(b.add(0xA1140+i*25),source.add(i*25));
 const initialize=new NativeFunction(b.add(0x42613),'void',['pointer','uint8'],'thiscall');
 for(let i=0;i<115;i++)initialize(b.add(0xB2C50+i*36),i);
 b.add(0xAC63C).writeU8(3);b.add(0xB5DF0).writeU32(65535);b.add(0xB5DF4).writeU32(65535);
 const dispatch=new NativeFunction(b.add(0x109EF),'uint',['pointer'],'fastcall'),rows=[];
 for(const emptyIndex of [0,5,199]){
  const common=b.add(0xB0770);common.writeByteArray(new Uint8Array(0x300).fill(165));
  const inventory=common.add(0x13);inventory.writeByteArray(new Uint8Array(600).fill(255));
  for(let i=0;i<emptyIndex;i++)inventory.add(i*3).writeByteArray([0,1,0]);
  const before=new Uint8Array(common.readByteArray(0x300));
  const obj=Memory.alloc(0x2040);obj.writeByteArray(new Uint8Array(0x2040));obj.add(12).writePointer(input);
  discoveries=[];prompts=[];
  const status=dispatch(obj)&255,after=new Uint8Array(common.readByteArray(0x300)),changes=[];
  for(let i=0;i<after.length;i++)if(before[i]!==after[i])changes.push({offset:i,before:before[i],after:after[i]});
  rows.push({emptyIndex,status,consumed:obj.add(12).readPointer().sub(input).toInt32(),
   entry:Array.from(new Uint8Array(inventory.add(emptyIndex*3).readByteArray(3))),changes,discoveries,prompts});
 }
 return rows;
}};
''');script.load();rows=script.exports_sync.verify(list(items),list(instruction))
        for row in rows:
            wanted=[dict(offset=0x13+row['emptyIndex']*3,before=255,after=76)]
            row['match']=(row['status']==1 and row['consumed']==len(instruction) and row['entry']==[76,255,255]
                          and row['changes']==wanted and row['discoveries']==[dict(index=79,value=1)])
        report=dict(source='S_00.eex opcode61 offset14459',item=76,name='太平清领道',
                    rows=rows,passed=all(r['match'] for r in rows),
                    scope='real DATA item loader, dispatcher/opcode61/0x45991B/0x40D79C; no live animation receiver; UI prompt and SVCMN discovery write intercepted; first/middle/final free slot only, overflow UI not tested')
        (ROOT/'analysis/native-s00-drop-inventory-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'S_00 drop to native inventory: {sum(r["match"] for r in rows)}/{len(rows)}')
        if not report['passed']:
            print(rows);raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
