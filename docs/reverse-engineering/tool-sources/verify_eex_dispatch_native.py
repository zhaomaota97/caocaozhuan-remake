"""Exercise non-UI EEX dispatcher cases in a suspended isolated executable."""
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
  const b=Process.mainModule.base;let audio=[];
  const music=new NativeCallback((_obj,track)=>{audio.push(['music',track]);},
    'void',['pointer','uint'],'thiscall');
  const stop=new NativeCallback(()=>{audio.push(['stop']);},'void',['pointer'],'fastcall');
  const sound=new NativeCallback((_obj,id,mode)=>{audio.push(['sound',id,mode]);},
    'void',['pointer','int','int'],'thiscall');
  const eventReset=new NativeCallback(()=>{audio.push(['event-reset']);},'void',['pointer'],'fastcall');
  const eventConfigure=new NativeCallback((_obj,value)=>{audio.push(['event-configure',value]);},
    'void',['pointer','int'],'thiscall');
  Interceptor.replace(b.add(0x745fe),music);Interceptor.replace(b.add(0x74619),stop);
  Interceptor.replace(b.add(0x74a07),sound);Interceptor.flush();
  Interceptor.replace(b.add(0x19fe2),eventReset);Interceptor.replace(b.add(0x19d22),eventConfigure);
  Interceptor.flush();
  const dispatch = new NativeFunction(Process.mainModule.base.add(0x109ef),
      'uint32', ['pointer'], 'fastcall');
  const tests = [
    {name:'end-0', bytes:[0,0], status:3, consumed:2},
    {name:'end-1', bytes:[1,0], status:4, consumed:2},
    {name:'status-6', bytes:[3,0], status:6, consumed:2},
    {name:'unknown', bytes:[255,0], status:5, consumed:2},
    {name:'skip-string', bytes:[2,0,5,0,65,66,0], status:1, consumed:7},
    {name:'wrong-string-tag', bytes:[2,0,4,0], status:5, consumed:4},
    {name:'choice-equal', bytes:[19,0,4,0,2,0,0,0], choice:2, status:1, consumed:8},
    {name:'choice-different', bytes:[19,0,4,0,3,0,0,0], choice:2, status:0, consumed:8},
    {name:'choice-wrong-tag', bytes:[19,0,5,0], choice:2, status:5, consumed:4},
    {name:'status-8', bytes:[12,0], status:8, consumed:2},
    {name:'flags-empty', bytes:[5,0,53,0,0,0,53,0,0,0], status:1, consumed:10},
    {name:'flags-true', bytes:[5,0,53,0,1,0,7,0,53,0,1,0,8,0],
      flags:[[7,9],[8,0]], status:1, consumed:14},
    {name:'flags-required-missing', bytes:[5,0,53,0,1,0,7,0,53,0,1,0,8,0],
      flags:[[7,0],[8,0]], status:0, consumed:14},
    {name:'flags-forbidden-set', bytes:[5,0,53,0,1,0,7,0,53,0,1,0,8,0],
      flags:[[7,9],[8,1]], status:0, consumed:14},
    {name:'flags-wrong-tag', bytes:[5,0,4,0], status:5, consumed:4},
    {name:'flags-clear-256', bytes:[10,0], flags:[[0,1],[255,2],[256,3]],
      after:[[0,0],[255,0],[256,3]], status:1, consumed:2},
    {name:'flag-set-normalizes', bytes:[11,0,4,0,7,0,0,0,39,0,9,0],
      after:[[7,1]], status:1, consumed:12},
    {name:'flag-clear-one', bytes:[11,0,4,0,7,0,0,0,39,0,0,0],
      flags:[[7,9],[8,6]], after:[[7,0],[8,6]], status:1, consumed:12},
    {name:'flag-invalid-index-tag', bytes:[11,0,5,0], status:5, consumed:4},
    {name:'flag-invalid-value-tag', bytes:[11,0,4,0,7,0,0,0,38,0],
      flags:[[7,9]], after:[[7,9]], status:5, consumed:10},
    {name:'music-first-track',bytes:[36,0,9,0,0,0],audio:[['music',2]],status:1,consumed:6},
    {name:'music-track-offset',bytes:[36,0,9,0,20,0],audio:[['music',22]],status:1,consumed:6},
    {name:'music-stop',bytes:[36,0,9,0,255,0],audio:[['stop']],musicState:255,status:1,consumed:6},
    {name:'music-wrong-tag',bytes:[36,0,4,0],status:5,consumed:4},
    {name:'sound-command',bytes:[35,0,30,0,207,0,4,0,3,0,0,0],
      audio:[['sound',207,3]],status:1,consumed:12},
    {name:'sound-wrong-mode-tag',bytes:[35,0,30,0,207,0,5,0],status:5,consumed:8},
    {name:'state-203c',bytes:[40,0,54,0,123,0],field203c:123,status:1,consumed:6},
    {name:'state-203c-wrong-tag',bytes:[40,0,4,0],field203c:0,status:5,consumed:4},
    {name:'event-latch-empty',bytes:[7,0],latch:0,status:0,consumed:2},
    {name:'event-latch-set',bytes:[7,0],latch:2,status:1,consumed:2}
  ];
  const word=v=>[v&255,(v>>>8)&255],dword=v=>[...word(v),...word(v>>>16)];
  for(const mode of [0,1,2,65535])for(const interval of [0,1,256,65535,0x12345678]){
    const first=[0,1,65535,32768,255],second=[7,8,9,10,11];
    const bytes=[6,0,...word(46),...word(mode),...word(4),...dword(interval),
      ...first.flatMap(v=>[...word(56),...word(v)]),
      ...second.flatMap(v=>[...word(57),...word(v)])];
    tests.push({name:'event-config-'+mode+'-'+interval,bytes,status:1,consumed:52,
      audio:mode===0?[['event-reset']]:[['event-configure',0]],
      eventInterval:(interval===0?1:interval)&255,eventParameters:[...first,...second]});
  }
  tests.push({name:'event-wrong-first-tag',bytes:[6,0,4,0],status:5,consumed:4});
  tests.push({name:'event-wrong-interval-tag',bytes:[6,0,46,0,0,0,5,0],status:5,consumed:8});
  const results = tests.map(t => {
    audio=[];b.add(0xae4c0).writeU32(t.latch || 0);b.add(0xb0770+4).writeU8(17);
    const obj = Memory.alloc(0x2040);
    obj.writeByteArray(new Uint8Array(0x2040));
    const input = Memory.alloc(t.bytes.length);
    input.writeByteArray(t.bytes);
    obj.add(0xc).writePointer(input);
    obj.add(0x2038).writeU32(t.choice || 0);
    for (const [i, value] of t.flags || []) obj.add(0x38 + i * 4).writeU32(value);
    const status = dispatch(obj) & 255;
    const consumed = obj.add(0xc).readPointer().sub(input).toInt32();
    const flagsMatch = (t.after || []).every(([i, value]) =>
      obj.add(0x38 + i * 4).readU32() === value);
    const stateMatch=(t.field203c===undefined || obj.add(0x203c).readU32()===t.field203c) &&
      (t.latch===undefined || b.add(0xae4c0).readU32()===0) &&
      (t.musicState===undefined || b.add(0xb0770+4).readU8()===t.musicState) &&
      (t.eventInterval===undefined || b.add(0xb09ec).readU8()===t.eventInterval) &&
      (t.eventParameters===undefined || t.eventParameters.every((v,i)=>b.add(0xb09f0+i*4).readU32()===v));
    const audioMatch=JSON.stringify(audio)===JSON.stringify(t.audio || []);
    return {name:t.name, status, consumed, flagsMatch,stateMatch,audio:audio.slice(),
      match:status === t.status && consumed === t.consumed && flagsMatch && stateMatch && audioMatch};
  });
  const block = new NativeFunction(Process.mainModule.base.add(0x1084e),
      'int', ['pointer','int','int'], 'thiscall');
  for (const length of [0, 2, 257]) {
    const obj = Memory.alloc(0x2040);
    obj.writeByteArray(new Uint8Array(0x2040));
    const input = Memory.alloc(length + 2);
    input.writeByteArray(new Uint8Array(length + 2));
    input.writeU16(length);
    obj.add(0xc).writePointer(input);
    obj.add(0x14).writeS32(-1);
    obj.add(0x28).writeU32(1);
    const status = block(obj, 0, 1);
    const consumed = obj.add(0xc).readPointer().sub(input).toInt32();
    const counter = obj.add(8).readU32();
    results.push({name:'skip-block-' + length, status, consumed, counter,
      match:status === 0 && consumed === length + 2 && counter === length + 2});
  }
  const execute = new NativeFunction(Process.mainModule.base.add(0x105a8),
      'int', ['pointer','int'], 'thiscall');
  for (const choice of [2, 3]) {
   for (const alternate of [false, true]) {
    const obj = Memory.alloc(0x2040);
    obj.writeByteArray(new Uint8Array(0x2040));
    obj.writePointer(Process.mainModule.base.add(0x86610));
    const bytes = [
      1,0, 19,0,4,0,2,0,0,0,
      14,0, 11,0,4,0,7,0,0,0,39,0,1,0, 0,0,
      3,0,
      14,0, 11,0,4,0,8,0,0,0,39,0,1,0, 0,0,
      0,0
    ];
    if (!alternate) bytes.splice(26, bytes.length - 26, 0, 0);
    const input = Memory.alloc(bytes.length);
    input.writeByteArray(bytes);
    const file = Memory.alloc(14);
    file.writeByteArray(new Uint8Array(14));
    file.add(10).writeU32(14);
    obj.add(0xc).writePointer(input);
    obj.add(0x14).writeS32(-1);
    obj.add(0x20).writePointer(file);
    obj.add(0x28).writeU32(1);
    obj.add(0x30).writeU32(10);
    obj.add(0x2038).writeU32(choice);
    const status = execute(obj, 1);
    const consumed = obj.add(0xc).readPointer().sub(input).toInt32();
    const thenFlag = obj.add(0x38 + 7 * 4).readU32();
    const elseFlag = obj.add(0x38 + 8 * 4).readU32();
    results.push({name:(alternate ? 'conditional-opcode3-rejected-' : 'conditional-') + choice,
      status, consumed, thenFlag, elseFlag,
      match:status === (alternate ? 1 : 0) && consumed === 28 &&
      thenFlag === (choice === 2 ? 1 : 0) && elseFlag === 0});
   }
  }
  return results;
}};
''')
        script.load()
        rows = script.exports_sync.verify()
        (ROOT / 'analysis/native-eex-dispatch-validation.json').write_text(
            json.dumps(rows, indent=2), encoding='utf-8')
        print(f'Native dispatcher checks: {sum(r["match"] for r in rows)}/{len(rows)}')
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
