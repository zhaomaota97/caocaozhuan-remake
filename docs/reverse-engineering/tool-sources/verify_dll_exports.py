import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
rows=json.loads((root/'analysis/dll-inventory.json').read_text(encoding='utf-8'))
auto=next(x for x in rows if x['file']=='AutoDLL.dll')
koe=next(x for x in rows if x['file']=='Koeicda.dll')
auto_names={x['name'] for x in auto['exports']}
koe_map={x['name']:x['rva'] for x in koe['exports']}
checks={
 'AutoDLL exports': auto_names=={'ASave','dummy'},
 'Koeicda export count': len(koe_map)==20,
 'Koeicda shared forwarders': sum(v==4480 for v in koe_map.values())==16,
 'Koeicda Pause RVA': koe_map.get('CDAudioPause')==4336,
 'Koeicda PlayTrack RVA': koe_map.get('CDAudioPlayTrack')==4368,
 'Koeicda Resume RVA': koe_map.get('CDAudioResume')==4416,
 'Koeicda Stop RVA': koe_map.get('CDAudioStop')==4448,
}
for name,ok in checks.items(): print(f'{name}: {"PASS" if ok else "FAIL"}')
if not all(checks.values()): raise SystemExit(1)
print('DLL export table validation: 7/7')
