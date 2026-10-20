"""Exercise native effect costs with rendering and progression callbacks suppressed."""
import json
from pathlib import Path
import frida

ROOT = Path(__file__).resolve().parents[1]


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
  const keep = [];
  // Suppress map selection, rendering, experience, equipment progression, refresh.
  for (const [rva, args, abi] of [
    [0x54f10,['pointer','int','int'],'thiscall'],
    [0x50984,['int','int','int','int','uint','uint','uint','int'],'mscdecl'],
    [0x8950,['pointer','uint','int'],'thiscall'],
    [0x82d6,['pointer','int','int'],'thiscall'],
    [0x79a01,['uint'],'mscdecl']
  ]) {
    const cb = new NativeCallback(function() {}, 'void', args, abi);
    keep.push(cb); Interceptor.replace(b.add(rva), cb);
  }
  Interceptor.flush();
  const apply = new NativeFunction(b.add(0x22f0d), 'void', ['pointer'], 'fastcall');
  const unit = b.add(0xa1b68);
  unit.writeByteArray(new Uint8Array(0x48));
  for (const offset of [0x2e,0x31,0x34]) unit.add(offset).writeU8(255);
  unit.add(0x1c).writeU32(100); unit.add(0x20).writeU8(50);
  const actor = Memory.alloc(0x24), action = Memory.alloc(0x4b0);
  const rows = [];
  for (const t of [
    {current:40,cost:13,expected:27},
    {current:5,cost:13,expected:0},
    {current:13,cost:13,expected:0},
    {current:40,cost:0,expected:40},
    {current:90,cost:0,expected:50},
    {current:40,cost:13,divisor:2,expected:34},
    {current:40,cost:13,divisor:3,expected:36},
    {current:40,cost:13,divisor:20,expected:40},
    {effect:20,current:40,cost:13,magnitude:7,expected:27,healthExpected:87},
    {effect:20,current:40,cost:13,magnitude:30,expected:27,healthExpected:100},
    {effect:22,current:40,cost:13,magnitude:7,expected:34},
    {effect:22,current:40,cost:13,magnitude:40,expected:50}
  ]) {
    actor.writeByteArray(new Uint8Array(0x24));
    actor.add(0x10).writeU32(80); actor.add(0x14).writeU32(t.current);
    action.writeByteArray(new Uint8Array(0x4b0));
    action.add(4).writePointer(unit); action.add(8).writePointer(actor);
    action.add(0x4ac).writeU32(1);
    action.writeU8(t.effect || 0);
    action.add(0x84).writeU32(t.magnitude || 0);
    unit.add(0x34).writeU8(t.divisor ? 0 : 255);
    if (t.divisor) {
      const item = b.add(0xa1140);
      item.writeByteArray(new Uint8Array(25));
      item.add(0x11).writeU8(0x31);
      item.add(0x15).writeU8(t.divisor);
    }
    b.add(0xaf4c0 + (t.effect || 0) * 70 + 14).writeU8(t.cost);
    apply(action);
    const resource = actor.add(0x14).readU32(), health = actor.add(0x10).readU32();
    rows.push({...t, resource, health,
      match:resource === t.expected && health === (t.healthExpected || 80)});
  }
  return rows;
}};
''')
        script.load()
        rows = script.exports_sync.verify()
        (ROOT / 'analysis/native-effect-cost-validation.json').write_text(
            json.dumps(rows, indent=2), encoding='utf-8')
        print(f'Native effect costs: {sum(r["match"] for r in rows)}/{len(rows)}')
        if not all(r['match'] for r in rows):
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
