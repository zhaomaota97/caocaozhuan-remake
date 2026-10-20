"""Link decoded battle-scene commands to native map IDs and artwork resources."""
import csv
import json
from pathlib import Path
import frida
from export_story_readable import walk
from export_eex_bodies import encode_instruction
from game_text import decode_game_text,visible_text

ROOT=Path(__file__).resolve().parents[1]


def main():
    assets={r['map_id']:r for r in json.loads((ROOT/'analysis/battle-maps/resource-links.json').read_text())}
    cases=[]
    for path in sorted((ROOT/'analysis/eex-bodies').glob('*.json')):
        if path.name=='summary.json':continue
        branches=json.loads(path.read_text(encoding='utf-8'));titles=[]
        for branch in branches:
            for node,_nested in walk(branch['nodes']):
                if node['opcode']==23:
                    titles.append(visible_text(decode_game_text(bytes.fromhex(node['arguments'][0]['hex']))))
        for branch in branches:
            for node,nested in walk(branch['nodes']):
                if node['opcode']!=39 or node['arguments'][0]['value']!=3:continue
                map_id=node['arguments'][4]['value']&255;asset=assets[map_id]
                cases.append(dict(script=f'{path.stem}.eex',segment=branch['segment'],branch=branch['branch'],
                    offset=node['offset'],map_id=map_id,titles=titles,nested=bool(nested),
                    artwork=asset['artwork'],palette=asset['palette_file'],palette_entry=asset['palette_entry'],
                    width=asset['width_tiles'],height=asset['height_tiles'],bytes=list(encode_instruction(node))))
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
  const b=Process.mainModule.base,obj=Memory.alloc(0x2040);
  const dispatch=new NativeFunction(b.add(0x109ef),'uint',['pointer'],'fastcall');
  return cases.map(c=>{
    b.add(0xac63c).writeU8(0);b.add(0xac63c+1).writeU8(55);b.add(0xb3d08).writeU8(77);
    b.add(0xabf9c).writeU32(0);
    const input=Memory.alloc(c.bytes.length);input.writeByteArray(c.bytes);
    obj.writeByteArray(new Uint8Array(0x2040));obj.add(12).writePointer(input);
    const status=dispatch(obj)&255;
    return {status,consumed:obj.add(12).readPointer().sub(input).toInt32(),
      mode:b.add(0xac63c).readU8(),commonIndex:b.add(0xac63c+1).readU8(),
      mapId:b.add(0xb3d08).readU8(),changed:b.add(0xabf9c).readU32()};
  });
}};
''')
        script.load();native=script.exports_sync.verify(cases)
        for case,actual in zip(cases,native):
            case['native_match']=(actual==dict(status=2,consumed=len(case['bytes']),mode=3,
                commonIndex=255,mapId=case['map_id'],changed=2))
            case.pop('bytes')
        (ROOT/'analysis/scenario-resource-links.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
        with (ROOT/'analysis/scenario-resource-links.csv').open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=list(cases[0]));writer.writeheader()
            for case in cases:writer.writerow(dict(case,titles=' / '.join(case['titles'])))
        print(f'Native scenario links: {sum(c["native_match"] for c in cases)}/{len(cases)}; '
              f'{len(set(c["map_id"] for c in cases))} unique maps')
        if len(cases)!=58 or not all(c['native_match'] for c in cases):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
