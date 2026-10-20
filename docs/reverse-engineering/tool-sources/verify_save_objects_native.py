"""Round-trip every shipped object through the original native save codecs."""
import json
from pathlib import Path
import frida

ROOT = Path(__file__).resolve().parents[1]


def main():
    device = frida.get_local_device()
    lab = ROOT / 'analysis' / 'runtime-game'
    pid = device.spawn([str(lab / 'Ekd5.exe')], cwd=str(lab))
    session = None
    try:
        session = device.attach(pid)
        script = session.create_script('''
rpc.exports = {verify(bytes) {
  const base = Process.mainModule.base;
  const load = new NativeFunction(base.add(0x9188), 'pointer',
      ['pointer', 'pointer'], 'thiscall');
  const save = new NativeFunction(base.add(0x8f2e), 'pointer',
      ['pointer', 'pointer'], 'thiscall');
  const input = Memory.alloc(bytes.length);
  input.writeByteArray(bytes);
  const obj = Memory.alloc(0x48);
  const out = Memory.alloc(32);
  let matches = 0;
  const failures = [];
  for (let i = 0; i < bytes.length / 32; i++) {
    obj.writeByteArray(new Uint8Array(0x48));
    const src = input.add(i * 32);
    const loaded = load(obj, src).sub(src).toInt32();
    const saved = save(obj, out).sub(out).toInt32();
    const actual = new Uint8Array(out.readByteArray(32));
    const equal = actual.every((v, j) => v === bytes[i * 32 + j]);
    if (loaded === 32 && saved === 32 && equal) matches++;
    else failures.push({index:i, loaded, saved, equal});
  }
  return {records:bytes.length / 32, matches, failures};
}};
''')
        script.load()
        results = []
        for path in sorted(ROOT.glob('Sv??d.e5s')):
            data = path.read_bytes()
            if len(data) != 0x54DC or data[0] != 5:
                raise ValueError(f'Unsupported save: {path.name}')
            result = script.exports_sync.verify(list(data[0x14DC:]))
            results.append(dict(file=path.name, **result))
        if not results:
            raise ValueError('No saves found')
        (ROOT / 'analysis' / 'native-save-object-validation.json').write_text(
            json.dumps(results, indent=2), encoding='utf-8')
        total = sum(row['records'] for row in results)
        matched = sum(row['matches'] for row in results)
        print(f'Native round-trip matches: {matched}/{total}')
        if matched != total:
            raise SystemExit(1)
    finally:
        try:
            device.kill(pid)
        except frida.ProcessNotFoundError:
            pass
        if session is not None:
            try:
                session.detach()
            except frida.InvalidOperationError:
                pass


if __name__ == '__main__':
    main()
