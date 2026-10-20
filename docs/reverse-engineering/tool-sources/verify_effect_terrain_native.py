"""Validate effect target eligibility on a constructed one-cell terrain map."""
import json
from pathlib import Path
import frida

ROOT = Path(__file__).resolve().parents[1]
GROUPS = [set([0,1,2,8,16,18,19,20,21,22,23,24]),
          set([7,8,9,10,13]), set([0,1,3,4,7,8,9,10,13]), set([3,4])]


def main():
    device = frida.get_local_device()
    lab = ROOT / 'analysis/runtime-game'
    pid = device.spawn([str(lab / 'Ekd5.exe')], cwd=str(lab))
    session = None
    try:
        session = device.attach(pid)
        script = session.create_script('''
rpc.exports = {verify() {
  const b = Process.mainModule.base;
  const check = new NativeFunction(b.add(0x20422), 'int',
      ['uint8','uint8','uint8','int'], 'mscdecl');
  const map = Memory.alloc(0x641);
  map.writeByteArray(new Uint8Array(0x641));
  const view = b.add(0xaeb38);
  view.add(4).writeU32(0x641); view.add(12).writePointer(map); view.add(16).writeU8(1);
  b.add(0xb422c).writeU8(1); b.add(0xb422d).writeU8(1);
  const actor = b.add(0xb2c50);
  actor.writeByteArray(new Uint8Array(0x48));
  const rows = [];
  for (let effect = 0; effect < 20; effect++) {
    for (let terrain = 0; terrain < 256; terrain++) {
      map.add(0x640).writeU8(terrain);
      rows.push({effect, terrain, accepted:check(effect, 0, 1, 0) !== 0});
    }
  }
  return rows;
}};
''')
        script.load()
        rows = script.exports_sync.verify()
        for row in rows:
            row['match'] = row['accepted'] == (row['terrain'] in GROUPS[row['effect']//5])
        (ROOT / 'analysis/native-effect-terrain-validation.json').write_text(
            json.dumps(rows, indent=2), encoding='utf-8')
        print(f'Native effect terrain checks: {sum(r["match"] for r in rows)}/{len(rows)}')
        if len(rows) != 5120 or not all(r['match'] for r in rows):
            raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:
                session.detach()
            except frida.InvalidOperationError:
                pass


if __name__ == '__main__':
    main()
