#!/usr/bin/env python3
import json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]; rows=[]
pat=re.compile(r'FUN_0041b51e\([^\n]*?,\s*([^,\)]+)\s*,')
for p in sorted((root/'analysis/native-main/pseudocode').glob('*.c')):
 text=p.read_text(encoding='utf-8',errors='replace')
 for m in pat.finditer(text): rows.append({'file':p.name,'line':text[:m.start()].count('\n')+1,'entry_expr':m.group(1).strip()})
out={'calls':rows,'literal_entries':sorted({int(r['entry_expr']) for r in rows if r['entry_expr'].isdigit()}),'nonliteral_entries':[r for r in rows if not r['entry_expr'].isdigit()]}
(root/'analysis/data-loader-calls.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
