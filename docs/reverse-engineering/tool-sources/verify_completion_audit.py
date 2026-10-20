#!/usr/bin/env python3
import re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
text=(root/'analysis/completion-audit.md').read_text(encoding='utf-8')
refs=set(re.findall(r'`([^`]+)`',text))
missing=[]
for ref in refs:
 if re.fullmatch(r'\d+/\d+',ref): continue
 if '/' not in ref and not ref.endswith(('.json','.md','.py')): continue
 candidates=[root/ref,root/'analysis'/ref,root/'tools'/ref]
 if not any(p.exists() for p in candidates): missing.append(ref)
print(f'audit references={len(refs)} missing={len(missing)}')
for x in sorted(missing): print('MISSING',x)
if missing: raise SystemExit(1)
