"""Verify 0x43FC48 resource-index mapping without loading or rendering effects."""
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]
TABLE=[5,5,5,0,1,2,6,7,8,3,4,5,9,10,11,18,19,20,12,13,14,15,16,17,
       21,22,23,24,25,26,27,28,29,23,23,23,14,14,14,33,34,32,31,30,23,23,
       39,35,36,37,38,68,69]


def main():
    cases=[dict(character_class=cls,slot5=slot,expected=(TABLE[cls]*3+min(slot,2) if TABLE[cls]<34 else TABLE[cls]+68))
           for cls in range(53) for slot in [0,1,2,3,7,255]]
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game';pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
 const b=Process.mainModule.base,unit=Memory.alloc(0x10),record=b.add(0xA1B68),rows=[];
 const keep=[]; const special=new NativeCallback(()=>-1,'int',['uint16'],'fastcall');keep.push(special);
 Interceptor.replace(b.add(0x6A75),special);Interceptor.flush();
 const select=new NativeFunction(b.add(0x3FC48),'uint',['pointer'],'fastcall');
 for(const c of cases){unit.writeByteArray(new Uint8Array(0x10));unit.writeU32(0);unit.add(5).writeU8(c.slot5);record.writeByteArray(new Uint8Array(0x48));record.add(0x2b).writeU8(c.character_class);rows.push(select(unit)&255);}
 return rows;
}};
''');script.load();actual=script.exports_sync.verify(cases)
        rows=[dict(**c,actual=a,match=a==c['expected']) for c,a in zip(cases,actual)]
        report=dict(function='0x43FC48',lookup='0x406947',passed=sum(r['match'] for r in rows),total=len(rows),rows=rows,
                    scope='all53 literal class-table entries ×6 slot+5 values; direct selector call; no resource loading, rendering or game resume')
        (ROOT/'analysis/native-unit-spc-mapping-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(f'Native Unit_spc index mapping: {report["passed"]}/{len(rows)}')
        if report['passed']!=len(rows):
            print(next(r for r in rows if not r['match']));raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
