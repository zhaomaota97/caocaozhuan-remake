"""Expand presets on each native map; isolate each level in a suspended process."""
import argparse
import ast
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit',type=int,default=58)
    args=parser.parse_args()
    tree=ast.parse((ROOT/'tools/capture_s00_expanded_units_native.py').read_text(encoding='utf-8'))
    js=next(n.args[0].value for n in ast.walk(tree) if isinstance(n,ast.Call)
            and isinstance(n.func,ast.Attribute) and n.func.attr=='create_script')
    tables=dict(entries(ROOT/'Data.e5'));terrain=dict(entries(ROOT/'Hexzmap.e5'))
    data={str(k):list(tables[k]) for k in (0,1,3,4)}
    source_index=json.loads((ROOT/'analysis/all-level-prefixes-native.json').read_text())['rows'][:args.limit]
    output=ROOT/'analysis/level-units-native';output.mkdir(exist_ok=True)
    dest=ROOT.parent/'caocaozhuan-remake/data/scenarios/native-units';dest.mkdir(exist_ok=True)
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game';rows=[]
    for item in source_index:
        name=Path(item['script']).stem
        source=json.loads((ROOT/'analysis/level-prefixes-native'/f'{name}.json').read_text(encoding='utf-8'))
        raw=terrain[item['mapId']];width,height=raw[0]//3,raw[1]//3
        if len(raw)!=2+width*height or width*height>1600:raise ValueError('Unsupported terrain size')
        pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
        try:
            session=device.attach(pid);script=session.create_script(js);script.load()
            result=script.exports_sync.capture(data,list(bytes.fromhex(source['stateHex'])),True,list(raw[2:]),[],[],False,False,None,[width,height])
            expected={u['battleSlot']:u for u in source['records']}
            checks=[];occupied=set()
            for unit in result['units']:
                fixture=expected[unit['slot']];hidden=fixture['initiallyHidden']
                position=unit['position'];key=tuple(position)
                # Native placement can relocate a requested coordinate if blocked.
                valid=(unit['type']==1 and position==[255,255]) if hidden else (
                    unit['type']==2 and 0<=position[0]<width and 0<=position[1]<height
                    and result['occupancy'][position[0]+position[1]*width]==unit['slot'] and key not in occupied)
                if not hidden:occupied.add(key)
                checks.append(dict(unitId=unit['unitId'],slot=unit['slot'],match=valid and unit['unitId']==fixture['unitId'],
                                   requested=fixture['coordinates'],actual=position,
                                   relocated=not hidden and fixture['coordinates']!=position))
            result.update(script=item['script'],mapId=item['mapId'],width=width,height=height,
                          checks=checks,passed=len(result['units'])==len(expected) and all(c['match'] for c in checks),
                          scope='real DATA loaders/0x44CC85/0x442B03 on actual map terrain; default Cao-only party, campaign chapter0 and original level preset fixture; UI/AI binding/mirror pixels suppressed; not post-map scripts or real campaign lineup')
            text=json.dumps(result,ensure_ascii=False,indent=2)
            (output/f'{name}.json').write_text(text,encoding='utf-8');(dest/f'{name}.json').write_text(text,encoding='utf-8')
            row=dict(script=item['script'],mapId=item['mapId'],units=len(result['units']),placed=len(occupied),
                     hidden=sum(u['type']==1 for u in result['units']),relocated=sum(c['relocated'] for c in checks),passed=result['passed'])
            rows.append(row);print(json.dumps(row),flush=True)
            if not result['passed']:raise ValueError(f'{name} actor placement check failed')
        finally:
            if session:session.detach()
            device.kill(pid)
    report=dict(levels=len(rows),passed=sum(r['passed'] for r in rows),rows=rows,
                scope='controlled default-party native expansions, not complete playable levels')
    text=json.dumps(report,indent=2)
    suffix='' if args.limit>=58 else '-sample'
    (ROOT/f'analysis/all-level-units-native{suffix}.json').write_text(text,encoding='utf-8')
    (dest/f'index{suffix}.json').write_text(text,encoding='utf-8')
    print(f'Native map expansions: {report["passed"]}/{len(rows)}',flush=True)


if __name__=='__main__':main()
