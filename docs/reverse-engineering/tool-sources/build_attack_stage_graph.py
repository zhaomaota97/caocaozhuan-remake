"""Emit the verified native attack stage order and source checks."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
stages=[
 {'order':1,'name':'initialize','rva':'0x4061fc','file':'004061fc.c'},
 {'order':2,'name':'generate-results','rva':'0x405e03','file':'00405e03.c'},
 {'order':3,'name':'present','rva':'0x405744','file':'00405744.c'},
 {'order':4,'name':'writeback','rva':'0x405889','file':'00405889.c'},
 {'order':5,'name':'repeat-decision','rva':'0x406181','file':'00406181.c'},
 {'order':6,'name':'attacker-reward','rva':'0x405c6c','file':'00405c6c.c'},
 {'order':7,'name':'counterattack-gate','rva':'0x40639a','file':'0040639a.c'},
]
for s in stages:s['sourceExists']=(ROOT/'analysis/native-main/pseudocode'/s['file']).exists()
out={'controller':'0x4064f1','stages':stages,'allSourcesExist':all(s['sourceExists'] for s in stages),'verifiedHelperGroups':['ordinary-damage','presentation-rng','automatic-healing','reward-controller','multi-target-reward','counterattack-gate']}
(ROOT/'analysis/native-attack-stage-graph.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
lines=['# Native attack stage graph','',f"Controller: `{out['controller']}`",'', '| Order | Stage | RVA | Pseudocode |', '|---:|---|---|---|']
for s in stages:
    lines.append(f"| {s['order']} | {s['name']} | `{s['rva']}` | `{s['file']}` |")
lines += ['', 'Verified helper groups: ' + ', '.join(f'`{x}`' for x in out['verifiedHelperGroups']), '', 'Every listed pseudocode source exists in the native analysis tree.']
(ROOT/'analysis/native-attack-stage-graph.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(f"Attack stages: {len(stages)}; source checks {'PASS' if out['allSourcesExist'] else 'FAIL'}")
if not out['allSourcesExist']:raise SystemExit(1)
