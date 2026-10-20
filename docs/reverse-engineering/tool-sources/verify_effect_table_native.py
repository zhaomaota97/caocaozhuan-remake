"""Validate the effect-record transform against the original native loader."""
import csv
import json
from pathlib import Path
import frida

ROOT = Path(__file__).resolve().parents[1]


def main():
    with (ROOT / 'analysis/effects.csv').open(encoding='utf-8-sig') as stream:
        records = list(csv.DictReader(stream))
    if len(records) != 73:
        raise ValueError('Run export_effect_table.py first; expected 73 records')
    device = frida.get_local_device()
    lab = ROOT / 'analysis/runtime-game'
    pid = device.spawn([str(lab / 'Ekd5.exe')], cwd=str(lab))
    session = None
    try:
        session = device.attach(pid)
        script = session.create_script('''
rpc.exports = {verify(records) {
  const load = new NativeFunction(Process.mainModule.base.add(0xddaf),
      'pointer', ['pointer','pointer'], 'thiscall');
  return records.map(record => {
    const input = Memory.alloc(70), output = Memory.alloc(70);
    input.writeByteArray(record);
    output.writeByteArray(new Uint8Array(70));
    const consumed = load(output, input).sub(input).toInt32();
    return {consumed, bytes:Array.from(new Uint8Array(output.readByteArray(70)))};
  });
}};
''')
        script.load()
        native = script.exports_sync.verify([list(bytes.fromhex(r['disk_hex'])) for r in records])
        results = [dict(id=i, consumed=n['consumed'],
                        match=n['consumed'] == 70 and bytes(n['bytes']).hex() == r['runtime_hex'])
                   for i, (r, n) in enumerate(zip(records, native))]
        (ROOT / 'analysis/native-effect-table-validation.json').write_text(
            json.dumps(results, indent=2), encoding='utf-8')
        print(f'Native effect records: {sum(r["match"] for r in results)}/{len(results)}')
        if not all(r['match'] for r in results):
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
