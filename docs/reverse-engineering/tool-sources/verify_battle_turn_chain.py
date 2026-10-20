#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sources={n:(root/'analysis/native-main/pseudocode'/f'{n}.c').read_text(encoding='utf-8') for n in ('004337f4','00433bc8')}
checks={}
for n,s in sources.items():
 checks[f'{n}_movement_entry']='FUN_00438308' in s
 checks[f'{n}_budget']='FUN_0043f74f' in s
 checks[f'{n}_battle_refresh']=('FUN_004539dc' in s and 'FUN_00453b13' in s)
for k,v in checks.items(): print(f'{k}: {"PASS" if v else "FAIL"}')
if not all(checks.values()): raise SystemExit(1)
