"""List recovered pseudocode routines that reference the battle map globals."""
from pathlib import Path
import re, json
ROOT=Path(__file__).resolve().parents[1]
targets=('b422c','b422d','B422C','B422D')
rows=[]
for p in sorted((ROOT/'analysis/native-main/pseudocode').glob('*.c')):
    text=p.read_text(encoding='utf-8',errors='ignore')
    hits=[]
    for i,line in enumerate(text.splitlines(),1):
        if any(t in line for t in targets): hits.append({'line':i,'text':line.strip()})
    if hits: rows.append({'routine':p.stem,'hits':hits})
(ROOT/'analysis/map-dimension-writers.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
lines=['# Battle map dimension cross-references','', 'Static pseudocode references to the recovered map width/height globals; assignment and read uses are retained verbatim for manual classification.', '']
for r in rows:
    lines.append(f"## `{r['routine']}`")
    for h in r['hits']: lines.append(f"- line {h['line']}: `{h['text']}`")
(ROOT/'analysis/map-dimension-writers.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('routines:',len(rows),'references:',sum(len(r['hits']) for r in rows))
