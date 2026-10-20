"""Differential-check level growth on temporary objects in the isolated game."""
import json
import time
from pathlib import Path
import frida
from character_growth import level_up
import struct
from extract_e5 import decode

root = Path(__file__).resolve().parent.parent
lab = root / 'analysis/runtime-game'
device = frida.get_local_device()
pid = device.spawn([str(lab / 'Ekd5.exe')], cwd=str(lab))
session = device.attach(pid)
script = session.create_script('''
rpc.exports = {verify(classGrowth) {
  const b = Process.mainModule.base;
  const table = b.add(0xabfa0+2);
  const original = table.readByteArray(7);
  table.writeByteArray(classGrowth);
  const grow = new NativeFunction(b.add(0x73b8), 'uint8', ['pointer','uint8','int'], 'thiscall');
  const rows = [];
  for (const test of [
    {stats:[10,20,30,40,50,100,25], bases:[24,25,34,35,45], level:1, steps:3},
    {stats:[254,254,254,254,254,499,249], bases:[45,45,45,45,45], level:49, steps:5},
    {stats:[10,10,10,10,10,10,10], bases:[24,25,35,44,45], level:50, steps:2}
  ]) {
    const obj = Memory.alloc(0x48);
    obj.writeByteArray(new Uint8Array(0x48));
    obj.add(0x2b).writeU8(0);
    obj.add(0x2c).writeU8(test.level);
    for (let i=0;i<5;i++) {obj.add(0x15+i).writeU8(test.stats[i]); obj.add(0x21+i).writeU8(test.bases[i]);}
    obj.add(0x1c).writeU32(test.stats[5]); obj.add(0x20).writeU8(test.stats[6]);
    const growth = Array.from(new Uint8Array(b.add(0xabfa0+2).readByteArray(7)));
    const returned = grow(obj, test.steps, 0);
    const stats = [];
    for(let i=0;i<5;i++) stats.push(obj.add(0x15+i).readU8());
    stats.push(obj.add(0x1c).readU32(), obj.add(0x20).readU8());
    rows.push({test, growth, stats, level:obj.add(0x2c).readU8(), returned});
  }
  table.writeByteArray(original);
  return rows;
}};
''')
try:
    script.load()
    device.resume(pid)
    time.sleep(3)
    data = (root / 'Data.e5').read_bytes()
    packed, size, offset = struct.unpack_from('>III', data, 0x110+3*12)
    class_growth = list(decode(data, offset, packed, size)[2:9])
    rows = script.exports_sync.verify(class_growth)
    for row in rows:
        test = row['test']
        stats, level = level_up(test['stats'], test['bases'], row['growth'], test['level'], test['steps'])
        row['match'] = stats == row['stats'] and level == row['level'] == row['returned']
    Path('analysis/native-growth-validation.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    print('native matches:', sum(r['match'] for r in rows), '/', len(rows))
    if not all(row['match'] for row in rows):
        raise SystemExit(1)
finally:
    try:
        device.kill(pid)
    except frida.ProcessNotFoundError:
        pass
    try:
        session.detach()
    except frida.InvalidOperationError:
        pass
