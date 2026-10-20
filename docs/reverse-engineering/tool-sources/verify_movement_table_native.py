"""Export terrain adaptation and validate native class mapping/movement costs."""
import csv
import json
import struct
from pathlib import Path
import frida
from extract_e5 import decode
from export_terrain_names import terrain_names

ROOT = Path(__file__).resolve().parents[1]


def movement_type(class_id):
    return class_id // 3 if class_id < 39 else class_id - 26 if class_id < 53 else 27


def main():
    data = (ROOT / 'Data.e5').read_bytes()
    packed, size, offset = struct.unpack_from('>III', data, 0x110 + 4 * 12)
    table = decode(data, offset, packed, size)
    if len(table) != 27 * 60:
        raise ValueError('Unexpected terrain table size')
    cases = []
    names = terrain_names()
    for cls in range(53):
        kind = movement_type(cls)
        for terrain in range(30):
            cost = table[kind * 60 + 30 + terrain]
            cases.append(dict(class_id=cls, movement_type=kind, terrain=terrain,
                              terrain_name=names[terrain],
                              adaptation=table[kind * 60 + terrain], cost=cost,
                              passable=cost != 255))
    device = frida.get_local_device()
    lab = ROOT / 'analysis/runtime-game'
    pid = device.spawn([str(lab / 'Ekd5.exe')], cwd=str(lab))
    session = None
    try:
        session = device.attach(pid)
        script = session.create_script('''
rpc.exports = {verify(table, cases) {
  const b = Process.mainModule.base;
  b.add(0xae4e0).writeByteArray(table);
  const unit = b.add(0xa1b68), actor = Memory.alloc(0x24);
  unit.writeByteArray(new Uint8Array(0x48));
  actor.writeByteArray(new Uint8Array(0x24));
  for (const off of [0x2e,0x31,0x34]) unit.add(off).writeU8(255);
  const kind = new NativeFunction(b.add(0x77d0), 'uint', ['pointer'], 'fastcall');
  const cost = new NativeFunction(b.add(0x3f7cf), 'uint', ['pointer','uint'], 'thiscall');
  const item = b.add(0xa1140);
  item.writeByteArray(new Uint8Array(25)); item.add(0x11).writeU8(0x22);
  return cases.map(c => {
    unit.add(0x2b).writeU8(c.class_id);
    unit.add(0x34).writeU8(255);
    const ordinary = cost(actor,c.terrain);
    unit.add(0x34).writeU8(0);
    return {kind:kind(unit), cost:ordinary, equipped:cost(actor,c.terrain)};
  });
}};
''')
        script.load()
        actual = script.exports_sync.verify(list(table), cases)
        if len(actual) != len(cases):
            raise ValueError('Native result count mismatch')
        for case, native in zip(cases, actual):
            case['native_type'] = native['kind']
            case['native_cost'] = native['cost']
            case['native_equipped_cost'] = native['equipped']
            case['match'] = (native['kind'] == case['movement_type'] and
                             native['cost'] == case['cost'] and
                             native['equipped'] == (255 if case['cost'] == 255 else 1))
        with (ROOT / 'analysis/class-terrain.csv').open('w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=list(cases[0]))
            writer.writeheader(); writer.writerows(cases)
        (ROOT / 'analysis/native-movement-table-validation.json').write_text(
            json.dumps(dict(cases=len(cases), matched=sum(c['match'] for c in cases),
                            failures=[c for c in cases if not c['match']]), indent=2), encoding='utf-8')
        print(f'Native movement checks: {sum(c["match"] for c in cases)}/{len(cases)}')
        if not all(c['match'] for c in cases):
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
