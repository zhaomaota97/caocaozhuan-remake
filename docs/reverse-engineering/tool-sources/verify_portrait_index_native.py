"""Compare the portrait selector against suspended native code without UI/audio."""
import json
from pathlib import Path

import frida
from export_portrait_index import portrait_index

ROOT = Path(__file__).resolve().parents[1]


def main():
    device = frida.get_local_device()
    runtime = ROOT / 'analysis/runtime-game'
    pid = device.spawn([str(runtime / 'Ekd5.exe')], cwd=str(runtime))
    session = None
    try:
        session = device.attach(pid)
        script = session.create_script('''
rpc.exports = { verify() {
 const base = Process.mainModule.base;
 const global = base.add(0xB0770);
 const unit = Memory.alloc(0x48);
 const select = new NativeFunction(base.add(0x75A7), 'int', ['pointer'], 'fastcall');
 const oldFlags = global.add(0x11).readU8(), oldPhase = global.add(6).readU8();
 const rows = [];
 try {
  for (const actor of [0, 1, 35, 8, 4, 2])
   for (const stored of [0, 8, 100, 220])
    for (const phase of [0, 1, 2, 255])
     for (let flags = 0; flags < 256; flags++) {
      unit.writeU16(actor); unit.add(4).writeS32(stored);
      global.add(0x11).writeU8(flags); global.add(6).writeU8(phase);
      rows.push([actor, stored, flags, phase, select(unit)]);
     }
 } finally { global.add(0x11).writeU8(oldFlags); global.add(6).writeU8(oldPhase); }
 return rows;
}};
''')
        script.load()
        rows = script.exports_sync.verify()
        failures = [r for r in rows if portrait_index(*r[:4]) != r[4]]
        report = dict(function='0x4075A7', mode='suspended process; never resumed',
                      cases=len(rows), passed=len(rows)-len(failures), failures=failures,
                      scope='six character identities, four stored indices, four phases, all flag bytes; selector only')
        (ROOT / 'analysis/native-portrait-index-validation.json').write_text(
            json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report))
        if failures:
            raise SystemExit(1)
    finally:
        if session:
            session.detach()
        device.kill(pid)


if __name__ == '__main__':
    main()
