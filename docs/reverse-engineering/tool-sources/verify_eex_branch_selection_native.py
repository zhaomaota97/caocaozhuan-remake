"""Validate candidate predicates, last-match priority, and selected body execution."""
import itertools
import json
import struct
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def build(predicates):
    segment=bytearray(struct.pack('<H',len(predicates)))
    cursors=[]
    for index,values in enumerate(predicates):
        predicate=b''.join(struct.pack('<HHI',19,4,v) for v in values)+b'\0\0'
        body=struct.pack('<HHIHHH',11,4,7+index,39,1,0)
        payload=predicate+struct.pack('<H',len(body))+body
        cursors.append(14+len(segment)+2+len(predicate))
        segment+=struct.pack('<H',len(payload))+payload
    return b'EEX\0\1\2\0\0\0\0'+struct.pack('<I',14)+segment,cursors


def main():
    cases=[]
    for predicates,choice in itertools.product([[[1],[2]],[[1],[1]],[[1,2],[1]],[[],[]]],range(3)):
        raw,cursors=build(predicates)
        accepted=[i for i,values in enumerate(predicates) if all(v==choice for v in values)]
        selected=accepted[-1] if accepted else None
        cases.append(dict(bytes=list(raw),predicates=predicates,choice=choice,
                          selected=selected,expected_cursor=cursors[selected] if selected is not None else None))
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
  const b=Process.mainModule.base;
  const select=new NativeFunction(b.add(0x100a1),'uint',['pointer'],'fastcall');
  const execute=new NativeFunction(b.add(0x1084e),'int',['pointer','int','int'],'thiscall');
  return cases.map(c=>{
    const file=Memory.alloc(c.bytes.length);file.writeByteArray(c.bytes);
    const obj=Memory.alloc(0x2040);obj.writeByteArray(new Uint8Array(0x2040));
    obj.writePointer(b.add(0x86610));obj.add(16).writeU16(65535);obj.add(20).writeS32(-1);
    obj.add(32).writePointer(file);obj.add(40).writeU32(1);obj.add(48).writeU32(10);
    obj.add(0x2038).writeU32(c.choice);
    const selected=select(obj),cursor=obj.add(12).readPointer().sub(file).toInt32();
    const bodyResult=selected?execute(obj,1,0):null;
    return {selected,cursor,bodyResult,flags:[obj.add(0x38+7*4).readU32(),obj.add(0x38+8*4).readU32()]};
  });
}};
''')
        script.load();native=script.exports_sync.verify(cases);rows=[]
        for case,actual in zip(cases,native):
            selected=case['selected'];flags=[int(selected==i) for i in range(2)]
            match=(actual['selected']==int(selected is not None) and actual['flags']==flags and
                   (selected is None or actual['cursor']==case['expected_cursor']) and
                   actual['bodyResult']==(None if selected is None else 0))
            rows.append(dict(predicates=case['predicates'],choice=case['choice'],
                             expected_branch=selected,actual=actual,match=match))
        (ROOT/'analysis/native-eex-branch-selection-validation.json').write_text(
            json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Native EEX branch selection: {sum(r["match"] for r in rows)}/{len(rows)}')
        if len(rows)!=12 or not all(r['match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
