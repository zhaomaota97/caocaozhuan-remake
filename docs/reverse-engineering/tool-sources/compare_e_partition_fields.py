"""Compare native E-partition structural fields across all ten slots."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
docs=[json.loads((ROOT/'analysis/runtime-game'/f'SV{i:02d}E.E5S.json').read_text()) for i in range(10)]
fields=['word0','byte4','byte5','word6','byte10','word11','byte13','byte14']
records=[]
for index in range(115):
    records.append({'index':index,'fields':{field:{'distinct':len({doc['records'][index][field] for doc in docs}),
      'values':[doc['records'][index][field] for doc in docs]} for field in fields}})
blocks=[]
for key in ['byte3d0e','byte3d0f','tail2038','tail203c']:
    blocks.append({'field':key,'distinct':len({doc[key] for doc in docs}),'values':[doc[key] for doc in docs]})
for key in ['block3d10','block3d04','aux10']:
    blocks.append({'field':key,'distinct':len({doc[key] for doc in docs}),'values':[doc[key] for doc in docs]})
result={'slots':10,'recordCount':115,'fields':fields,'records':records,'fixedBlocks':blocks}
(ROOT/'analysis/e-partition-field-differences.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
variable=sum(1 for row in records if any(v['distinct']>1 for v in row['fields'].values()))
print(f'E partition field comparison: {variable}/115 records vary across slots')
