"""Summarize value ranges in E records without assigning semantic names."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
docs=[json.loads((ROOT/'analysis/runtime-game'/f'SV{i:02d}E.E5S.json').read_text()) for i in range(10)]
fields=['word0','byte4','byte5','word6','byte10','word11','byte13','byte14']
result={'slots':10,'records':115,'fields':{}}
for field in fields:
 values=[record[field] for doc in docs for record in doc['records']]
 result['fields'][field]={'min':min(values),'max':max(values),'distinct':sorted(set(values)),
                           'nonzero':sum(value!=0 for value in values)}
(ROOT/'analysis/e-partition-value-ranges.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('E partition range summary written')
