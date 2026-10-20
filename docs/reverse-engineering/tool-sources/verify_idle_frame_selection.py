"""Exercise the original frame selector; stub only direction and health predicates."""
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
rpc.exports = {verify() {
  const b=Process.mainModule.base, actor=b.add(0xb2c50);
  let direction=0, injured=0, offset=-1;
  const directionCallback=new NativeCallback(()=>direction,'uint',['pointer'],'fastcall');
  const injuredCallback=new NativeCallback(()=>injured,'uint',['pointer','uint'],'fastcall');
  const viewCallback=new NativeCallback((_view,off)=>{offset=off;return ptr(0x100000);},'pointer',['pointer','uint','int','int'],'thiscall');
  Interceptor.replace(b.add(0x3e320),directionCallback);
  Interceptor.replace(b.add(0x4015a),injuredCallback);
  Interceptor.replace(b.add(0x7fa40),viewCallback);
  Interceptor.flush();
  const select=new NativeFunction(b.add(0x3e572),'pointer',['int'],'mscdecl');
  const rows=[];
  for(direction=0;direction<4;direction++)for(injured=0;injured<2;injured++)
    for(const flags of [0,2,4,6])for(const status of [0,2])for(let phase=0;phase<8;phase++){
      actor.writeByteArray(new Uint8Array(36));actor.add(13).writeU8(flags);actor.add(30).writeU8(status);
      b.add(0xb3d0d).writeU8(phase);offset=-1;select(0);
      rows.push({direction,injured,flags,status,phase,tile:offset/2304});
    }
  return rows;
}};
''')
    script.load()
    rows = script.exports_sync.verify()
    for row in rows:
        bank = [1, 2, 0, 2][row['direction']]
        special = bool(row['flags'] & 6)
        expected = 9 if row['injured'] else bank + 6 if special else bank * 2
        if not special:
            expected += int(row['phase'] >= 4) if row['status'] & 2 else row['phase'] & 1
        row['expected'] = expected
        row['match'] = row['tile'] == expected
    result = {'scope': 'Original 0x43e572; direction/health predicates stubbed, phase and flag reads original',
              'cases': len(rows), 'matched': sum(r['match'] for r in rows), 'rows': rows}
    (ROOT / 'analysis/native-idle-frame-validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f"Native idle frame selector: {result['matched']}/{result['cases']}")
    if result['matched'] != result['cases']:
        raise SystemExit(1)
finally:
    device.kill(pid)
    if session:
        session.detach()
