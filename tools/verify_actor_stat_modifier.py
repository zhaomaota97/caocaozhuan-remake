"""Call native 0x43F54C in a suspended process, without starting game UI/audio."""
import json
from pathlib import Path
import frida

ROOT = Path(__file__).resolve().parents[1]
device = frida.get_local_device()
pid = device.spawn([str(ROOT / 'analysis/runtime-game/Ekd5.exe')], cwd=str(ROOT / 'analysis/runtime-game'))
session = None
try:
    session = device.attach(pid)
    script = session.create_script('''
rpc.exports={capture(){
 const modifier=new NativeFunction(Process.mainModule.base.add(0x3f54c),'uint',['uint','uint8'],'mscdecl');
 const rows=[];
 for(const base of [0,1,2,3,7,9,10,11,99,100,101,249,250,255,299,300,333,399,400,500])
 for(let status=0;status<256;status++)rows.push({base,status,result:modifier(base,status)});
 return rows;
}};
''')
    script.load()
    rows = script.exports_sync.capture()
    failures = [row for row in rows if row['result'] != (row['base'] * 7 // 10 if row['status'] < 3 else row['base'] if row['status'] == 3 else row['base'] * 12 // 10)]
    report = dict(address='0x43F54C', scope='leaf integer status modifier; not equipment aggregation or presentation', passed=not failures, count=len(rows), rows=rows)
    text = json.dumps(report, indent=2) + '\n'
    (ROOT / 'analysis/native-actor-stat-modifier.json').write_text(text, encoding='utf-8')
    (ROOT.parent / 'caocaozhuan-remake/docs/reverse-engineering/native-actor-stat-modifier.json').write_text(text, encoding='utf-8')
    print(f'Native actor stat modifier: {len(rows)-len(failures)}/{len(rows)}')
    if failures:
        raise RuntimeError(failures[0])
finally:
    device.kill(pid)
    if session:
        session.detach()
