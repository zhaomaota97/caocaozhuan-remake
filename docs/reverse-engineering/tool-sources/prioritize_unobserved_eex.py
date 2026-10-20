"""Rank EEX handlers not yet seen in bounded live runs."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rows=json.loads((ROOT/'analysis/eex-handler-semantics.json').read_text(encoding='utf-8'))
seen=set(json.loads((ROOT/'analysis/live-eex-opcode-union.json').read_text(encoding='utf-8'))['union'])
out=[]
for row in rows:
    if row['opcode'] in seen or row.get('classification')=='reserved/terminal': continue
    score=(len(row.get('suspected_global_writes',[]))*3+
           len(row.get('called_functions',[]))*2+
           (1 if row.get('parameter_tags') else 0))
    out.append({'opcode':row['opcode'],'handler':row['handler'],'score':score,
                'classification':row.get('classification'),
                'parameterTags':row.get('parameter_tags'),
                'globalWrites':row.get('suspected_global_writes',[]),
                'calledFunctions':row.get('called_functions',[])})
out.sort(key=lambda row:(-row['score'],row['opcode']))
(ROOT/'analysis/unobserved-eex-priority.json').write_text(json.dumps({'observed':sorted(seen),'candidates':out},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('unobserved EEX candidates:',len(out))
print('top:',[(x['opcode'],x['score']) for x in out[:10]])
