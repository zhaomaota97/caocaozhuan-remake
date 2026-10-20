#!/usr/bin/env python3
import csv,json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
rows=[]
for r in csv.DictReader((root/'analysis/eex/opcode-index.csv').open(encoding='utf-8-sig')):
 op=int(r['opcode']); h=r['handler'].lower(); fn=h+'.c'; p=root/'analysis/native-main/pseudocode'/fn
 text=p.read_text(encoding='utf-8',errors='replace') if p.exists() else ''
 calls=sorted(set(re.findall(r'FUN_([0-9a-fA-F]{8})\s*\(',text)))
 globals=sorted(set(re.findall(r'DAT_([0-9a-fA-F]{8})|s_([A-Za-z0-9_]+)_([0-9A-Fa-f]{8})',text)))
 g=[]
 for x in globals:
  g.extend([v for v in x if v])
 writes=sorted(set(re.findall(r'(?:DAT_|_DAT_)([0-9A-Fa-f]{8})\s*(?:\[.*?\])?\s*(?:=|\|=|&=|\+=|-=)',text)))
 rows.append({'opcode':op,'handler':h,'classification':r.get('classification',''),'parameter_tags':r.get('parameter_tags',''),'pseudocode_exists':bool(text),'called_functions':calls,'global_tokens':g,'suspected_global_writes':writes})
(root/'analysis/eex-handler-semantics.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'handlers={len(rows)} pseudocode={sum(x["pseudocode_exists"] for x in rows)}')
