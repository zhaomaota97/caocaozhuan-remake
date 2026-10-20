"""Run a bounded Frida investigation against an isolated game copy."""
import argparse
import json
import shutil
import time
import ctypes
from pathlib import Path

import frida


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seconds', type=int, default=25)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    lab = root / 'analysis' / 'runtime-game'
    lab.mkdir(parents=True, exist_ok=True)
    for source in root.iterdir():
        if source.is_file() and source.suffix.lower() in {
            '.exe', '.dll', '.ini', '.dat', '.txt', '.e5', '.eex', '.e5s', '.wav', '.avi'
        }:
            target = lab / source.name
            if not target.exists():
                shutil.copy2(source, target)
    if (root / 'SoundTrk').exists():
        shutil.copytree(root / 'SoundTrk', lab / 'SoundTrk', dirs_exist_ok=True)
    log = root / 'analysis' / ('runtime-' + time.strftime('%Y%m%d-%H%M%S') + '.jsonl')
    device = frida.get_local_device()
    pid = device.spawn([str(lab / 'Ekd5.exe')], cwd=str(lab))
    session = None
    with log.open('w', encoding='utf-8') as stream:
        def message(value, data=None):
            if data is not None:
                payload = value.get('payload', {})
                name = 'dump-' + str(payload.get('sequence', 0)) + '.bin'
                dump = log.parent / (log.stem + '-' + name)
                dump.write_bytes(data)
                payload['dump_path'] = str(dump)
            stream.write(json.dumps(value, ensure_ascii=False) + '\n')
            stream.flush()
            print(json.dumps(value, ensure_ascii=False), flush=True)
        try:
            session = device.attach(pid)
            script = session.create_script('''
const base = Process.mainModule.base;
send({event:'attached', pid:Process.id, arch:Process.arch, base:base.toString()});
function hook(name, onEnter, onLeave) {
  let p = null;
  try { p = Module.getGlobalExportByName(name); } catch (e) {}
  send({event:'hook-status', name:name, address:p ? p.toString() : null});
  if (p) Interceptor.attach(p, {onEnter, onLeave});
}
hook('CreateFileW', function(args) {
  try { send({event:'CreateFileW', path:args[0].readUtf16String(), access:args[1].toString()}); } catch(e) {}
});
hook('CreateFileA', function(args) {
  try { send({event:'CreateFileA', path:args[0].readCString(), access:args[1].toString()}); } catch(e) {}
});
hook('ReadFile', function(args) {
  try { send({event:'ReadFile', handle:args[0].toString(), size:args[2].toInt32()}); } catch(e) {}
});
hook('SetFilePointer', function(args) {
  try { send({event:'SetFilePointer', handle:args[0].toString(), distance:args[1].toInt32(), mode:args[3].toInt32()}); } catch(e) {}
});
hook('LoadLibraryW', function(args) {
  try { send({event:'LoadLibraryW', path:args[0].readUtf16String()}); } catch(e) {}
});
hook('LoadLibraryA', function(args) {
  try { send({event:'LoadLibraryA', path:args[0].readCString()}); } catch(e) {}
});
Process.setExceptionHandler(function(e) {
  send({event:'exception', type:e.type, address:e.address.toString()});
  return false;
});
let resourceEvents = 0;
const containers = new Map();
Interceptor.attach(base.add(0x1fb35), {onEnter(args) {
  try {containers.set(this.context.ecx.toString(), args[0].readCString());} catch(e) {}
}});
let dumpSequence = 0;
Interceptor.attach(base.add(0x1fc89), {onEnter(args) {
  this.container = containers.get(this.context.ecx.toString());
  this.index = args[0].toUInt32();
  this.output = args[1];
}, onLeave(result) {
  const size = result.toUInt32();
  if (!this.output.isNull() && size > 0 && size <= 16777216 && dumpSequence < 100) {
    try {send({event:'decoded-resource', container:this.container, index:this.index,
      size:size, sequence:dumpSequence++}, this.output.readByteArray(size));} catch(e) {send({event:'dump-error', error:String(e)});}
  }
}});
for (const offset of [0x10273, 0x17ed2, 0x1fb35, 0x1a1b0, 0x1b606, 0x08be3, 0x19102, 0x191af]) {
  Interceptor.attach(base.add(offset), {onEnter(args) {
    if ((offset === 0x1b606 || offset === 0x08be3) && resourceEvents++ > 200) return;
    const item = {event:'entry', rva:offset, ecx:this.context.ecx.toString(), arg0:args[0].toString()};
    if (offset === 0x1b606) { item.resource_id = args[1].toUInt32(); item.resource_source = args[0].toString(); }
    if (offset === 0x08be3) { item.resource_id = args[0].toUInt32(); }
    if (offset === 0x1a1b0) { item.save_index = args[0].toUInt32(); item.save_value = args[1].toUInt32(); }
    if (offset === 0x19102) { item.read_size = args[1].toUInt32(); }
    if (offset === 0x191af) { item.distance = args[0].toInt32(); item.origin = args[1].toInt32(); }
    if (offset === 0x1fa24 || offset === 0x1f9b0) {
      if ((Process.getCurrentThreadId() & 31) !== 0) return;
    }
    if (offset === 0x10273) {
      try {item.header = Array.from(new Uint8Array(args[0].readByteArray(64)));} catch(e) {item.error=String(e);}
    }
    send(item);
  }});
}
''')
            script.on('message', message)
            session.on('detached', lambda reason, crash: message({'event':'detached', 'reason':reason, 'crash':str(crash)}))
            script.load()
            device.resume(pid)
            # Give the legacy GUI a chance to reach its title/menu loop.
            time.sleep(3)
            # Legacy title screens commonly accept Enter/Escape; send a small
            # bounded sequence to expose an existing save without modifying it.
            user32 = ctypes.windll.user32
            hwnds = []
            enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            def collect(hwnd, _):
                owner = ctypes.c_ulong()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
                if owner.value == pid:
                    hwnds.append(hwnd)
                return True
            user32.EnumWindows(enum_proc(collect), 0)
            candidates = []
            for hwnd in hwnds:
                buf = ctypes.create_unicode_buffer(256)
                user32.GetWindowTextW(hwnd, buf, 256)
                title = buf.value
                message({'event':'window', 'hwnd':int(hwnd), 'title':title})
                if title and 'PRESS.AVI' not in title and 'IME' not in title and 'MSCTF' not in title:
                    candidates.append(hwnd)
            if candidates:
                user32.ShowWindow(candidates[-1], 5)
                user32.SetForegroundWindow(candidates[-1])
            for vk in (0x0D, 0x0D, 0x4C, 0x30, 0x0D, 0x1B):
                user32.keybd_event(vk, 0, 0, 0)
                user32.keybd_event(vk, 0, 2, 0)
                time.sleep(1)
            time.sleep(args.seconds)
        finally:
            try:
                device.kill(pid)
            except frida.ProcessNotFoundError:
                pass
            if session:
                try:
                    session.detach()
                except frida.InvalidOperationError:
                    pass
    print('Evidence:', log)


if __name__ == '__main__':
    main()
