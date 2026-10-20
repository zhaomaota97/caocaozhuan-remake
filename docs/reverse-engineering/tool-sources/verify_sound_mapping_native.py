"""Capture original sound-wrapper filenames without playing audio."""
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
  const api = Module.getGlobalExportByName('sndPlaySoundA');
  let paths = [];
  const capture = new NativeCallback((path, flags) => {
    if (!path.isNull()) paths.push({path:path.readCString(), flags});
    return 1;
  }, 'int', ['pointer','uint'], 'stdcall');
  Interceptor.replace(api, capture);
  Interceptor.flush();
  const play = new NativeFunction(b.add(0x74777), 'int',
      ['pointer','int','int','int'], 'thiscall');
  const obj = Memory.alloc(8);
  const rows = [];
  b.add(0xb0770).writeU16(0x1000);
  for (let id = 0; id <= 209; id++) {
    obj.writeS32(-1); obj.add(4).writeU32(0); paths = [];
    const returned = play(obj, id, 65535, 0);
    rows.push({id, returned, paths});
  }
  obj.writeS32(-1); obj.add(4).writeU32(1); paths = [];
  rows.push({name:'busy-gate', returned:play(obj, 0, 65535, 0), paths});
  obj.add(4).writeU32(0); b.add(0xb0770).writeU16(0); paths = [];
  rows.push({name:'disabled-gate', returned:play(obj, 0, 65535, 0), paths});
  return rows;
}};
''')
        script.load()
        rows = script.exports_sync.verify()
        for row in rows:
            index = row.get('id', -1)
            expected = (f'SE{index:02d}.WAV' if 0 <= index <= 42 else
                        f'SE_M_{index-100:02d}.WAV' if 100 <= index <= 136 else
                        f'SE_E_{index-200:02d}.WAV' if 200 <= index <= 208 else None)
            paths = row['paths']
            if expected is None:
                row['match'] = row['returned'] == 0 and not paths
            else:
                row['expected'] = expected
                row['file_exists'] = (ROOT / expected).is_file()
                row['match'] = (row['returned'] == 1 and len(paths) == 1 and
                                paths[0]['path'].replace('\\', '/').split('/')[-1].upper() == expected and
                                paths[0]['flags'] == 3 and row['file_exists'])
        (ROOT / 'analysis/native-sound-mapping-validation.json').write_text(
            json.dumps(rows, indent=2), encoding='utf-8')
        print(f'Sound mapping checks: {sum(r["match"] for r in rows)}/{len(rows)}')
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
