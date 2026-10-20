"""Validate a recorded actual GUI load using native returns, I/O, and window captures."""
import json
import sys
from pathlib import Path,PureWindowsPath

ROOT=Path(__file__).resolve().parents[1]


def summarize(folder,slot):
    records=[json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
    payloads=[r.get('payload',{}) for r in records]
    entered=[p for p in payloads if p.get('event')=='native-entry' and p.get('rva')==0x1ad06]
    returned=[p for p in payloads if p.get('event')=='native-return' and p.get('rva')==0x1ad06]
    paths=[p['path'] for p in payloads if p.get('event')=='CreateFileA']
    names={PureWindowsPath(p).name.upper() for p in paths}
    map_id=(ROOT/f'Sv{slot:02d}s.e5s').read_bytes()[35]
    required=[f'SV{slot:02d}{part}.E5S' for part in 'DES']+[
        f'HM{map_id:02d}.E5','HEXZMAP.E5','SPALET.E5','UNIT_MOV.E5']
    expected_slot=(len(entered)==1 and int(entered[0]['arg0'],16)==slot)
    result=dict(slot=slot,map_id=map_id,correct_native_slot=expected_slot,
        intro_skipped=any(p.get('event')=='intro-skipped' for p in payloads),
        load_returned_success=bool(returned and int(returned[-1]['value'],16)==1),
        confirmed_from_ui=any(r.get('event')=='action' and r.get('name')=='confirm-load' and r.get('slot')==slot for r in records),
        required_resources={name:name in names for name in required},
        battle_setup_seen=any(p.get('event')=='native-entry' and p.get('rva')==0x4d092 for p in payloads),
        terrain_loader_seen=any(p.get('event')=='native-entry' and p.get('rva')==0x4c1cb for p in payloads),
        save_function_called=any(p.get('event')=='native-entry' and p.get('rva')==0x1b16a for p in payloads),
        captures=[p.name for p in sorted(folder.glob('window-*.png'))])
    result['passed']=(result['correct_native_slot'] and result['load_returned_success'] and
        result['confirmed_from_ui'] and all(result['required_resources'].values()) and
        result['battle_setup_seen'] and result['terrain_loader_seen'] and not result['save_function_called'])
    (folder/'load-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    result=summarize(Path(sys.argv[1]),int(sys.argv[2]))
    print(f'Actual GUI load verified: {result["passed"]}; slot {result["slot"]}, map {result["map_id"]}')
    if not result['passed']:raise SystemExit(1)
