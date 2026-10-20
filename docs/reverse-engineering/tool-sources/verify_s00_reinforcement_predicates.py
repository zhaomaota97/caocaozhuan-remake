"""Check original first-three S_00 event predicates through native selection."""
import itertools
import json
import struct
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def main():
    source=(ROOT/'S_00.eex').read_bytes()
    predicates=[p for p in json.loads((ROOT/'analysis/eex-predicates/S_00.json').read_text(encoding='utf-8')) if p['segment']==1 and p['branch']<3]
    segment=bytearray(struct.pack('<H',3));cursors=[]
    for p in predicates:
        raw=source[p['instructions'][0]['offset']:p['body_offset']-2]
        # Predicate includes its original terminating opcode0; body is not run.
        payload=raw+struct.pack('<HH',2,0)
        cursors.append(14+len(segment)+2+len(raw))
        segment+=struct.pack('<H',len(payload))+payload
    file=b'EEX\0\1\2\0\0\0\0'+struct.pack('<I',14)+segment
    cases=[]
    for turn,phase,mask,mode in itertools.product(range(3),range(3),range(16),(0,3)):
        accepted=[]
        if turn==0 and not mask&8:accepted.append(0)
        if turn==0 and phase==2 and mode==3 and not mask&1:accepted.append(1)
        if turn==1 and not mask&6:accepted.append(2)
        cases.append(dict(turn=turn,phase=phase,mask=mask,mode=mode,expected=accepted[-1] if accepted else None))
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(bytes,cases,cursors){
 const b=Process.mainModule.base,input=Memory.alloc(bytes.length);input.writeByteArray(bytes);
 const select=new NativeFunction(b.add(0x100A1),'uint',['pointer'],'fastcall');
 return cases.map(c=>{
  const obj=Memory.alloc(0x2040);obj.writeByteArray(new Uint8Array(0x2040));
  obj.writePointer(b.add(0x86610));obj.add(16).writeU16(65535);obj.add(20).writeS32(-1);
  obj.add(32).writePointer(input);obj.add(40).writeU32(1);obj.add(48).writeU32(10);
  [11,12,13,14].forEach((flag,i)=>obj.add(0x38+flag*4).writeU32((c.mask>>i)&1));
  b.add(0xB3D0A).writeU8(c.turn);b.add(0xB3D18).writeU8(c.phase);b.add(0xAC63C).writeU8(c.mode);
  const selected=select(obj),cursor=obj.add(12).readPointer().sub(input).toInt32();
  return {selected,branch:selected?cursors.indexOf(cursor):null};
 });
}};
''');script.load();actual=script.exports_sync.verify(list(file),cases,cursors)
        rows=[dict(**c,actual=a,match=a['selected']==int(c['expected'] is not None) and a['branch']==c['expected']) for c,a in zip(cases,actual)]
        report=dict(total=len(rows),passed=sum(r['match'] for r in rows),rows=rows,
                    scope='original raw predicates of S_00 segment1 branches0/1/2 only; native parser/turn/phase/flags/last-match selector; bodies not executed, remaining15 branches excluded')
        (ROOT/'analysis/native-s00-reinforcement-predicates.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(f'S_00 reinforcement predicate selection: {report["passed"]}/{len(rows)}')
        if report['passed']!=len(rows):
            print(next(r for r in rows if not r['match']));raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
