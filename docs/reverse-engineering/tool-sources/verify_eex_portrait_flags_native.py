"""Validate opcode32 writes through the native EEX dispatcher; index script uses."""
import json
import struct
from pathlib import Path
import frida
from export_story_readable import walk

ROOT = Path(__file__).resolve().parents[1]


def main():
    values = [0, 1, 2, 3, 4, 16, 32, 64, 128, 255, 256, 511, 32768, 65535]
    cases = []
    for seed in range(256):
        for value in values:
            for tag in (73, 74, 75):
                expected = seed if tag != 74 or value == 32768 else seed & 224 if value & 255 == 255 else (seed & 240) | (value & 255)
                cases.append(dict(seed=seed, value=value, tag=tag, expected=expected,
                                  bytes=list(struct.pack('<HHH', 32, tag, value))))
    occurrences = []
    for path in sorted((ROOT / 'analysis/eex-bodies').glob('*.json')):
        if path.name == 'summary.json':
            continue
        for branch in json.loads(path.read_text(encoding='utf-8')):
            for node, conditions in walk(branch['nodes']):
                if node['opcode'] == 32:
                    occurrences.append(dict(file=path.name, segment=branch['segment'],
                                            branch=branch['branch'], offset=node['offset'],
                                            arguments=node['arguments'], conditions=conditions))
    device = frida.get_local_device()
    runtime = ROOT / 'analysis/runtime-game'
    pid = device.spawn([str(runtime / 'Ekd5.exe')], cwd=str(runtime))
    session = None
    try:
        session = device.attach(pid)
        script = session.create_script('''
rpc.exports = {verify(cases) {
 const b=Process.mainModule.base,obj=Memory.alloc(0x2040),input=Memory.alloc(6);
 const dispatch=new NativeFunction(b.add(0x109EF),'uint',['pointer'],'fastcall');
 const common=b.add(0xB0770), original=common.readByteArray(64),rows=[];
 try {
  for(const c of cases) {
   common.writeByteArray(new Uint8Array(64).fill(165));common.add(17).writeU8(c.seed);
   input.writeByteArray(c.bytes);obj.writeByteArray(new Uint8Array(0x2040));obj.add(12).writePointer(input);
   const status=dispatch(obj)&255, after=new Uint8Array(common.readByteArray(64));
   let adjacent=0;for(let i=0;i<64;i++)if(i!==17&&after[i]!==165)adjacent++;
   rows.push({seed:c.seed,value:c.value,tag:c.tag,flags:after[17],status,
    consumed:obj.add(12).readPointer().sub(input).toInt32(),adjacent});
  }
 } finally {common.writeByteArray(original);}
 return rows;
}};
''')
        script.load()
        rows = script.exports_sync.verify(cases)
        for case, row in zip(cases, rows):
            row['expected'] = case['expected']
            row['match'] = (row['flags'] == case['expected'] and row['adjacent'] == 0
                            and row['status'] == (5 if case['tag'] != 74 or case['value'] == 32768 else 1)
                            and row['consumed'] == (6 if case['tag'] == 74 else 4))
        report = dict(opcode=32, handler='0x416FD8', dispatcher='0x4109EF',
                      scope='all256 previous flag bytes,14 parameter values,3 tags; real parser and setter; suspended process',
                      passed=sum(r['match'] for r in rows), total=len(rows), rows=rows,
                      script_occurrences=occurrences,
                      script_scope='decoded static references; conditions recorded, execution not proven')
        (ROOT / 'analysis/native-eex-portrait-flags-validation.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Native EEX portrait flags: {report["passed"]}/{len(rows)}; {len(occurrences)} script references')
        if report['passed'] != len(rows):
            print(next(r for r in rows if not r['match']))
            raise SystemExit(1)
    finally:
        if session:
            session.detach()
        device.kill(pid)


if __name__ == '__main__':
    main()
