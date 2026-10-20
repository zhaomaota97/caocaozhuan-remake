"""Join EEX opcode index with native validation artifacts."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((ROOT/'analysis/eex/opcode-index.csv').open(encoding='utf-8-sig')))
evidence={}
for p in (ROOT/'analysis').glob('native-eex*.json'):
 try:data=json.loads(p.read_text(encoding='utf-8'))
 except Exception:continue
 stack=[data]
 while stack:
  value=stack.pop()
  if isinstance(value,dict):
   if 'opcode' in value:
    try:evidence.setdefault(int(value['opcode']),[]).append(p.name)
    except (TypeError,ValueError):pass
   stack.extend(value.values())
  elif isinstance(value,list):stack.extend(value)
matrix=[]
for row in rows:
 op=int(row['opcode']);handler=row['handler']
 status='reserved' if row['classification']=='reserved/terminal' else ('dynamic' if op in evidence else 'static')
 matrix.append({'opcode':op,'handler':handler or None,'classification':row['classification'],'status':status,'evidence':sorted(set(evidence.get(op,[])))})
out={'total':len(matrix),'dynamic':sum(x['status']=='dynamic' for x in matrix),'static':sum(x['status']=='static' for x in matrix),'reserved':sum(x['status']=='reserved' for x in matrix),'rows':matrix}
(ROOT/'analysis/eex-coverage-matrix.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
lines=['# EEX opcode coverage matrix','',f"Total {out['total']}; dynamic artifacts {out['dynamic']}; static-only {out['static']}; reserved {out['reserved']}.",'', '| Opcode | Handler | Status | Evidence |','|---:|---|---|---|']
for x in matrix:
 lines.append(f"| {x['opcode']} | `{x['handler'] or '-'}` | **{x['status']}** | {', '.join('`'+e+'`' for e in x['evidence']) or '-'} |")
(ROOT/'analysis/eex-coverage-matrix.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(f"EEX matrix: dynamic={out['dynamic']} static={out['static']} reserved={out['reserved']}")
