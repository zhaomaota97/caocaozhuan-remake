"""Verify phase writes via original opcode58/103 with title drawing intercepted."""
import json
from pathlib import Path
import frida
from export_eex_bodies import encode_instruction
from export_story_readable import walk

ROOT = Path(__file__).resolve().parents[1]


def copy_title(raw):
    out = bytearray()
    i = 0
    while i < len(raw) and raw[i]:
        if raw[i] == 10 and raw[i:i+2] == b'\n&':
            break
        size = 1 if raw[i] < 32 else 2
        out.extend(raw[i:i+size])
        i += size
    return out.hex()


def make_case(node, origin):
    value = node['arguments'][0]['value'] if node['opcode'] == 103 else node['arguments'][2]['value']
    invalid = node['opcode'] == 103 and value & 65535 == 32768
    expected = 165 if invalid else max((value & 255)-1, 0) if node['opcode'] == 103 else value & 255
    return dict(opcode=node['opcode'], value=value, origin=origin,
                expected=expected, invalid=invalid, bytes=list(encode_instruction(node)),
                title=copy_title(bytes.fromhex(node['arguments'][1]['hex']))
                if node['opcode'] == 103 and not invalid else None)


def main():
    cases = []
    references = []
    for path in sorted((ROOT / 'analysis/eex-bodies').glob('*.json')):
        if path.name == 'summary.json':
            continue
        for branch in json.loads(path.read_text(encoding='utf-8')):
            for node, conditions in walk(branch['nodes']):
                if node['opcode'] not in (58, 103):
                    continue
                ref = dict(file=path.name, segment=branch['segment'], branch=branch['branch'],
                           offset=node['offset'], opcode=node['opcode'],
                           arguments=node['arguments'], conditions=conditions)
                references.append(ref)
                if node['opcode'] == 103 or node['arguments'][0]['value'] == 1:
                    cases.append(make_case(node, ref))
    for value in list(range(256)) + [256, 511, 32768, 65535, 65536, 0x12348000]:
        for title in (b'\xd0\xf2', b'\xd0\xf2\n&\xd0\xf2'):
            node = dict(opcode=103, arguments=[dict(tag=4,value=value),dict(tag=5,hex=title.hex())])
            cases.append(make_case(node, 'synthetic'))
        for option in (0, 1, 65535):
            node = dict(opcode=58,arguments=[dict(tag=40,value=1),dict(tag=52,value=option),dict(tag=4,value=value)])
            cases.append(make_case(node, 'synthetic'))
    device = frida.get_local_device()
    runtime = ROOT / 'analysis/runtime-game'
    pid = device.spawn([str(runtime / 'Ekd5.exe')], cwd=str(runtime))
    session = None
    try:
        session = device.attach(pid)
        script = session.create_script('''
rpc.exports={verify(cases){
 const b=Process.mainModule.base,common=b.add(0xB0770),old=common.readByteArray(64);
 const obj=Memory.alloc(0x2040),dispatch=new NativeFunction(b.add(0x109EF),'uint',['pointer'],'fastcall');
 let events=[];
 const titleSink=new NativeCallback((value,text)=>{
  const bytes=[];for(let i=0;i<1024;i++){const x=text.add(i).readU8();if(!x)break;bytes.push(x);}
  events.push({value,hex:bytes.map(x=>x.toString(16).padStart(2,'0')).join('')});
 },'void',['uint8','pointer'],'mscdecl');
 Interceptor.replace(b.add(0x0B940),titleSink);Interceptor.flush();
 const rows=[];
 try{for(const c of cases){
  const input=Memory.alloc(c.bytes.length);input.writeByteArray(c.bytes);
  obj.writeByteArray(new Uint8Array(0x2040));obj.add(12).writePointer(input);
  common.writeByteArray(new Uint8Array(64).fill(165));events=[];
  const status=dispatch(obj)&255,after=new Uint8Array(common.readByteArray(64));
  let adjacent=0;for(let i=0;i<64;i++)if(i!==6&&after[i]!==165)adjacent++;
  rows.push({status,phase:after[6],adjacent,consumed:obj.add(12).readPointer().sub(input).toInt32(),events});
 }}finally{common.writeByteArray(old);}
 return rows;
}};
''')
        script.load()
        rows = script.exports_sync.verify(cases)
        for case, row in zip(cases, rows):
            events = [dict(value=case['value'] & 255, hex=case['title'])] if case['title'] is not None else []
            case['actual'] = row
            case['match'] = (row['phase'] == case['expected'] and row['adjacent'] == 0
                             and row['status'] == (5 if case['invalid'] else 1)
                             and row['consumed'] == (8 if case['invalid'] else len(case['bytes']))
                             and row['events'] == events)
        result = dict(passed=sum(c['match'] for c in cases), total=len(cases), rows=cases,
                      script_references=references,
                      scope='native dispatcher/parser/setters and opcode103 title copier; title drawing replaced; opcode58 only field selector1; static references do not prove story execution')
        (ROOT / 'analysis/native-eex-portrait-phase-validation.json').write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Native EEX portrait phase: {result["passed"]}/{len(cases)}; {len(references)} static opcode58/103 references')
        if result['passed'] != len(cases):
            print(next(c for c in cases if not c['match']))
            raise SystemExit(1)
    finally:
        if session:
            session.detach()
        device.kill(pid)


if __name__ == '__main__':
    main()
