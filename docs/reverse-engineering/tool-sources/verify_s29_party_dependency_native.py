"""Measure party-size dependencies of S_29 setup and slot-based appearance."""
import ast
import json
import struct
from pathlib import Path
import frida
from export_eex_bodies import encode_block,encode_instruction
from export_map_layouts import entries
from export_story_readable import walk

ROOT=Path(__file__).resolve().parents[1]


def literal(path):
    return next(n.args[0].value for n in ast.walk(ast.parse(path.read_text(encoding='utf-8')))
                if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='create_script')


def main():
    branches=json.loads((ROOT/'analysis/eex-bodies/S_29.json').read_text(encoding='utf-8'))
    root=branches[0];scene=next(n for n in root['nodes'] if n['opcode']==39)
    prefix=encode_block(dict(nodes=[n for n in root['nodes'] if n['offset']<=scene['offset']]+[dict(opcode=0)]))
    predicate=struct.pack('<HH',2,5)+b'\0'+b'\0\0';payload=predicate+struct.pack('<H',len(prefix))+prefix
    file=b'EEX\0\1\2\0\0\0\0'+struct.pack('<I',14)+struct.pack('<HH',1,len(payload))+payload
    appearances=[dict(offset=n['offset'],bytes=list(encode_instruction(n))) for n,c in walk(root['nodes'])
                 if n['opcode']==76 and n['arguments'][0]['value']==1]
    tables=dict(entries(ROOT/'Data.e5'));terrain=dict(entries(ROOT/'Hexzmap.e5'))[29]
    data={str(k):list(tables[k]) for k in (0,1,3,4)}
    prefix_js=literal(ROOT/'tools/export_all_level_prefixes_native.py')
    expansion_js=literal(ROOT/'tools/capture_s00_expanded_units_native.py')
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game';rows=[]
    for party in ([0],[0,2,21],[0,2,21,15,1]):
        pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
        try:
            session=device.attach(pid);script=session.create_script(prefix_js);script.load()
            case=dict(script='S_29.eex',bytes=list(file))
            prefix_result=script.exports_sync.verify([case],party)[0]
            primary=[r for r in prefix_result['records'] if r['flags']&3==0]
            script.unload()
            expanded=session.create_script(expansion_js);expanded.load()
            result=expanded.exports_sync.capture(data,list(bytes.fromhex(prefix_result['stateHex'])),True,list(terrain[2:]),
                                                  appearances,[],False,False,None,[terrain[0]//3,terrain[1]//3])
            active=[u for u in result['units'] if u['slot']<15 and u['type']==2]
            changes=[r['changes'] for r in result['appearanceResults']]
            expected_slots=list(range(len(party)))
            row=dict(party_fixture=party,prefix_selected=prefix_result['selected'],prefix_result=prefix_result['result'],
                     preset_count=len(prefix_result['records']),primary=[dict(id=r['unitId'],position=r['coordinates']) for r in primary],
                     appearance_results=result['appearanceResults'],active_primary=[dict(slot=u['slot'],id=u['unitId'],position=u['position']) for u in active],
                     no_op_appearances=sum(not c for c in changes))
            row['passed']=(row['prefix_selected']==1 and row['prefix_result']==2 and [r['id'] for r in row['primary']]==party
                           and [u['slot'] for u in active]==expected_slots and [u['unitId'] for u in active]==party
                           and row['no_op_appearances']==5-len(party))
            rows.append(row);print(f'S_29 party {party}: presets={row["preset_count"]}, active={len(active)}, no-op={row["no_op_appearances"]}, passed={row["passed"]}',flush=True)
        finally:
            if session:session.detach()
            device.kill(pid)
    report=dict(passed=all(r['passed'] for r in rows),rows=rows,
                scope='original S29 prefix interpreter with explicit1/3/5-member parties; real DATA unit expansion/coordinate entry and individual slot0..4 appearance handlers; story conditions and intervening moves/dialogue not executed; fixtures not canonical campaign teams')
    (ROOT/'analysis/native-s29-party-dependency.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
