"""Execute every original S_00 node through its map-transition boundary."""
import json
import struct
from pathlib import Path
import frida
from export_eex_bodies import encode_block

ROOT=Path(__file__).resolve().parents[1]


def main():
    branch=json.loads((ROOT/'analysis/eex-bodies/S_00.json').read_text(encoding='utf-8'))[0]
    nodes=[n for n in branch['nodes'] if n['offset']<=6144]
    body=encode_block(dict(nodes=nodes+[dict(opcode=0)]))
    original=(ROOT/'S_00.eex').read_bytes()[35:6166]
    if body[:-2]!=original:
        raise ValueError('Prefix differs from original EEX bytes')
    predicate=struct.pack('<HH',2,5)+b'\0'+b'\0\0'
    payload=predicate+struct.pack('<H',len(body))+body
    file=b'EEX\0\1\2\0\0\0\0'+struct.pack('<I',14)+struct.pack('<HH',1,len(payload))+payload
    capture=json.loads((ROOT/'analysis/native-s00-unit-setup-replay.json').read_text())
    # Last selected write is opcode72; source captures opcode75 only, so recover
    # its later write deltas before comparing the complete record table.
    expected=bytearray(next(r['state_after'] for r in reversed(capture['rows']) if r.get('state_after')))
    last_snapshot=max(i for i,r in enumerate(capture['rows']) if r.get('state_after'))
    for event in capture['rows'][last_snapshot+1:]:
        for change in event['changed']:
            expected[change['offset']]=change['after']
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(bytes){
 const b=Process.mainModule.base,input=Memory.alloc(bytes.length),obj=Memory.alloc(0x2040);
 input.writeByteArray(bytes);obj.writeByteArray(new Uint8Array(0x2040));
 obj.writePointer(b.add(0x86610));obj.add(16).writeU16(65535);obj.add(20).writeS32(-1);
 obj.add(32).writePointer(input);obj.add(40).writeU32(1);obj.add(48).writeU32(10);
 const visits=[];
 Interceptor.attach(b.add(0x109EF),{onEnter(){const o=this.context.ecx;visits.push(o.add(12).readPointer().readU16());}});
 const select=new NativeFunction(b.add(0x100A1),'uint',['pointer'],'fastcall');
 const execute=new NativeFunction(b.add(0x1084E),'int',['pointer','int','int'],'thiscall');
 const selected=select(obj),result=execute(obj,1,0);
 return {selected,result,visits,mode:b.add(0xAC63C).readU8(),mapId:b.add(0xB3D08).readU8(),
  records:Array.from(new Uint8Array(b.add(0x92F90+0x2044).readByteArray(115*64)))};
}};
''');script.load();actual=script.exports_sync.verify(list(file))
        raw=bytes(actual.pop('records'));wanted=bytes(expected[0x2044:0x2044+115*64])
        differences=[dict(offset=i,expected=e,actual=a) for i,(e,a) in enumerate(zip(wanted,raw)) if e!=a]
        report=dict(source='S_00.eex offsets35..6166',original_prefix_byte_exact=True,
                    actual=actual,record_bytes=len(raw),record_differences=differences,
                    passed=actual['selected']==1 and actual['result']==2 and actual['mode']==3
                    and actual['mapId']==0 and not differences,
                    scope='all original nodes through scene-transition opcode39, real selector/interpreter/conditions/handlers; fresh suspended globals; no character-table or campaign initialization; not post-transition battlefield')
        (ROOT/'analysis/native-s00-entry-prefix-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(f'S_00 full entry prefix: passed={report["passed"]}; result={actual["result"]}; record differences={len(differences)}; visits={actual["visits"]}')
        if not report['passed']:raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
