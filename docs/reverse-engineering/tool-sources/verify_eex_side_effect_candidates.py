#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
rows=json.loads((root/'analysis/eex-handler-semantics.json').read_text(encoding='utf-8'))
expected={6:{'004b09ec'},7:{'004ae4c0'},39:{'004abf9c','004b3d08'},69:{'00494fd0','00496c94','00496c96','00496c98','00496c9a','00496c9f','00496e21','00496e22','00496e23'},91:{'004b3d10','004b3d14','004b3d15','004b3d16','004b3d17'},93:{'004b3d0b'},106:{'004b3d10'}}
actual={x['opcode']:set(x['suspected_global_writes']) for x in rows if x['suspected_global_writes']}
checks={op:actual.get(op)==vals for op,vals in expected.items()}
for op,ok in checks.items(): print(f'opcode_{op}: {"PASS" if ok else "FAIL"} {sorted(actual.get(op,set()))}')
print(f'candidates={len(actual)} expected={len(expected)}')
if actual != expected: raise SystemExit(1)
