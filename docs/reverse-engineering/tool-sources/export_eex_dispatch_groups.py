#!/usr/bin/env python3
import csv,json,sys
from collections import Counter
from pathlib import Path
if len(sys.argv)!=3: raise SystemExit('usage: export_eex_dispatch_groups.py events.jsonl output.csv')
c=Counter()
for line in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines():
 try: p=json.loads(line).get('payload',{})
 except: continue
 if p.get('event')=='eex-dispatch':
  stack=tuple(x.get('address') for x in p.get('stack',[]))
  c[(p.get('arg0'),p.get('arg1'),p.get('arg2'),p.get('return_address'),stack)]+=1
with Path(sys.argv[2]).open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f); w.writerow(['count','arg0','arg1','arg2','return_address','stack'])
 for (a,b,d,r,s),n in c.most_common(): w.writerow([n,a,b,d,r,';'.join(s)])
print(f'groups={len(c)} calls={sum(c.values())} output={sys.argv[2]}')
