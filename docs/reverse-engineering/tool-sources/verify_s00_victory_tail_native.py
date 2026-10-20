"""Run byte-exact S_00 reward/end tail, replacing only result-window rendering."""
import itertools
import json
import struct
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def main():
    original=(ROOT/'S_00.eex').read_bytes()
    body=original[14255:14333]
    predicate=struct.pack('<HH',2,5)+b'\0'+b'\0\0'
    payload=predicate+struct.pack('<H',len(body))+body
    file=b'EEX\0\1\2\0\0\0\0'+struct.pack('<I',14)+struct.pack('<HH',1,len(payload))+payload
    cases=[dict(level=level,money=money) for level,money in itertools.product((1,7,31,50),(0,1234,999950,999999))]
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(bytes,cases){
 const b=Process.mainModule.base,input=Memory.alloc(bytes.length);input.writeByteArray(bytes);
 const keep=[],displayCalls=[];
 const display=new NativeCallback((money,items,mode)=>{displayCalls.push({money,items:Array.from(new Uint8Array(items.readByteArray(3))),mode});},'void',['int','pointer','uint'],'mscdecl');
 keep.push(display);Interceptor.replace(b.add(0x4B5A8),display);Interceptor.flush();
 const select=new NativeFunction(b.add(0x100A1),'uint',['pointer'],'fastcall');
 const execute=new NativeFunction(b.add(0x1084E),'int',['pointer','int','int'],'thiscall');
 return cases.map(c=>{
  const obj=Memory.alloc(0x2040);obj.writeByteArray(new Uint8Array(0x2040));
  obj.writePointer(b.add(0x86610));obj.add(16).writeU16(65535);obj.add(20).writeS32(-1);
  obj.add(32).writePointer(input);obj.add(40).writeU32(1);obj.add(48).writeU32(10);
  b.add(0xA1B68+44).writeU8(c.level);b.add(0xB0770+12).writeU32(c.money);
  b.add(0xAC63C).writeU8(3);b.add(0xB3D08+1).writeU8(0);b.add(0xB0770+2).writeU16(123);
  const index=displayCalls.length,selected=select(obj),result=execute(obj,1,0);
  return {selected,result,money:b.add(0xB0770+12).readU32(),battleState:b.add(0xB3D08+1).readU8(),
   commonState:b.add(0xB0770+2).readU16(),flags:[0,100,600].map(i=>obj.add(0x38+i*4).readU32()),
   display:displayCalls.slice(index)};
 });
}};
''');script.load();actual=script.exports_sync.verify(list(file),cases)
        rows=[]
        for case,row in zip(cases,actual):
            reward=case['level']*100+700
            checks=dict(money=row['money']==min(999999,case['money']+reward),
                        state=row['battleState']==2 and row['commonState']==0,
                        flags=row['flags']==[1,1,1],
                        display=row['display']==[dict(money=reward,items=[255,255,255],mode=0)],
                        selected=row['selected']==1)
            rows.append(dict(input=case,reward=reward,actual=row,checks=checks,match=all(checks.values())))
        report=dict(source_offsets=[14255,14333],rows=rows,passed=sum(r['match'] for r in rows),total=len(rows),
                    scope='original victory tail opcode89/73/11/13 through native selector/interpreter; result window callback only; seeded Cao level and treasury; no preceding dialogue/retreat, inventory awards, full branch selection or campaign transition')
        (ROOT/'analysis/native-s00-victory-tail-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(f'S_00 reward/end tail: {report["passed"]}/{len(rows)}; returns={sorted({r["actual"]["result"] for r in rows})}')
        if report['passed']!=len(rows):
            print(next(r for r in rows if not r['match']));raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
