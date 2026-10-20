"""Verify MP3Serv's native track indexing while replacing audio playback."""
import hashlib
import json
import subprocess
from pathlib import Path
import frida

ROOT = Path(__file__).resolve().parents[1]


def main():
    executable = ROOT / 'analysis/mp3serv-unpacked.exe'
    lines = (ROOT / 'mp3list.txt').read_text(encoding='ascii').splitlines()
    device = frida.get_local_device()
    pid = device.spawn([str(executable)], cwd=str(ROOT))
    session = None
    try:
        session = device.attach(pid)
        script = session.create_script('''
rpc.exports = {verify(lines) {
  const b = Process.mainModule.base;
  let selected = null;
  const capture = new NativeCallback(function(path) {
    selected = path.readCString();
  }, 'void', ['pointer'], 'mscdecl');
  Interceptor.replace(b.add(0x17ef), capture);
  Interceptor.flush();
  const entries = Memory.alloc(lines.length * 28);
  entries.writeByteArray(new Uint8Array(lines.length * 28));
  const keep = [];
  lines.forEach((line, i) => {
    const entry = entries.add(i * 28);
    if (line.length >= 16) {
      const str = Memory.allocUtf8String(line);
      keep.push(str);
      entry.add(4).writePointer(str);
      entry.add(24).writeU32(line.length);
    } else {
      entry.add(4).writeUtf8String(line);
      entry.add(24).writeU32(15);
    }
    entry.add(20).writeU32(line.length);
  });
  b.add(0xcaf8).writePointer(entries);
  b.add(0xcafc).writePointer(entries.add(lines.length * 28));
  const proc = new NativeFunction(b.add(0x1d6b), 'int',
      ['pointer','uint','uint','int'], 'stdcall');
  const rows = [];
  for (let track = 0; track <= lines.length + 1; track++) {
    selected = null;
    proc(ptr(0), 0x1979, track, 0);
    const expected = track > 1 && track <= lines.length ? lines[track - 1] : null;
    rows.push({track, selected, expected, match:selected === expected});
  }
  return rows;
}};
''')
        script.load()
        rows = script.exports_sync.verify(lines)
        result = dict(executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
                      playlist_lines=len(lines), source='constructed playlist vector; native WndProc',
                      rows=rows)
        (ROOT / 'analysis/native-music-mapping-validation.json').write_text(
            json.dumps(result, indent=2), encoding='utf-8')
        rizin = r'C:\Program Files\Rizin\bin\rizin.exe'
        disassembly = subprocess.run([rizin, '-e', 'scr.color=0', '-q', '-c',
            'pd 115 @ 0x401d6b', str(executable)], capture_output=True, check=True)
        (ROOT / 'analysis/mp3serv-message-disassembly.txt').write_bytes(disassembly.stdout)
        print(f'Music mapping checks: {sum(r["match"] for r in rows)}/{len(rows)}')
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
