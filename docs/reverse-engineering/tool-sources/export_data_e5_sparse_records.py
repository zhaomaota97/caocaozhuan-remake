"""Export Data.e5 entries 6-9 as neutral fixed-width record evidence."""
import csv, json
from pathlib import Path
from export_map_layouts import entries
ROOT = Path(__file__).resolve().parents[1]
rows=[]
for idx, raw in entries(ROOT/'Data.e5'):
    if idx < 6: continue
    for width in (17, 21):
        count, rem = divmod(len(raw), width)
        if count:
            for n in range(count):
                chunk=raw[n*width:(n+1)*width]
                rows.append({'entry':idx,'width':width,'record':n,'offset':n*width,
                             'hex':chunk.hex(),'all_zero':not any(chunk),
                             'distinct_values':','.join(map(str,sorted(set(chunk))))})
            if rem:
                tail=raw[-rem:]
                rows.append({'entry':idx,'width':width,'record':'tail','offset':count*width,
                             'hex':tail.hex(),'all_zero':not any(tail),
                             'distinct_values':','.join(map(str,sorted(set(tail))))})
with (ROOT/'analysis/data-e5-sparse-records.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=['entry','width','record','offset','hex','all_zero','distinct_values']); w.writeheader(); w.writerows(rows)
summary={}
for r in rows:
    key=f"{r['entry']}:{r['width']}"; summary.setdefault(key,{'records':0,'tails':0,'signatures':set()})
    if r['record']=='tail': summary[key]['tails']+=1
    else: summary[key]['records']+=1; summary[key]['signatures'].add(r['hex'])
for v in summary.values(): v['distinct_signatures']=len(v.pop('signatures'))
(ROOT/'analysis/data-e5-sparse-records.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print('exported',len(rows),'record rows')
