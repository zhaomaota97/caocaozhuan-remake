"""Verify native 50ms frame-clock arithmetic and reference counter."""
import itertools
import ctypes
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def main():
    cases=[dict(now=now,target=target,expected=((target-now)&0xFFFFFFFF if ctypes.c_int32(now).value < ctypes.c_int32(target).value else 0))
           for now,target in itertools.product((0,1,10,100,0xFFFFFFFF),(0,1,9,10,11,100,0xFFFFFFFF))]
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game';pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
 const b=Process.mainModule.base,keep=[],clock=Memory.alloc(4),now=Memory.alloc(4),ref=b.add(0xBC018),redraw=new NativeCallback(()=>{},'void',['int','int','int','int','int'],'mscdecl');
 const tick=new NativeCallback(()=>now.readU32(),'uint',[],'mscdecl');keep.push(redraw,tick);Interceptor.replace(b.add(0x7C966),redraw);Interceptor.replace(b.add(0x7EB97),tick);Interceptor.flush();
 const diff=new NativeFunction(b.add(0x2C479),'int',['pointer'],'fastcall');const hold=new NativeFunction(b.add(0x7EBA5),'uint',['int'],'mscdecl');const rows=[];
 for(const c of cases){now.writeU32(c.now);clock.writeU32(c.target);rows.push({now:c.now,target:c.target,actual:diff(clock)});}
 const refs=[];ref.writeU32(0);for(const op of [0,0,0,1,1,1])refs.push({op,active:hold(op),value:ref.readU32()});return {rows,refs};
}};
''');script.load();native=script.exports_sync.verify(cases)
        rows=[dict(**c,actual=n['actual'],match=c['expected']==n['actual']) for c,n in zip(cases,native['rows'])]
        expected_refs=[dict(op=op,active=active,value=value) for op,active,value in [(0,1,1),(0,1,2),(0,1,3),(1,1,2),(1,1,1),(1,0,0)]]
        report=dict(functions=['0x42C479','0x47EBA5'],passed=sum(r['match'] for r in rows),total=len(rows),rows=rows,
                    reference_counter=native['refs'],reference_expected=expected_refs,
                    reference_match=native['refs']==expected_refs,
                    scope='controlled GetTickCount/50ms return; wait arithmetic and reference counter, redraw callback replaced')
        (ROOT/'analysis/native-frame-clock-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(f'Native frame clock: {report["passed"]}/{len(rows)}; ref={report["reference_match"]}')
        if report['passed']!=len(rows) or not report['reference_match']:raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
