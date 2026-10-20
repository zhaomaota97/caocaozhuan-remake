import csv, json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
rows=[]
for module in json.loads((root/'analysis/dll-inventory.json').read_text(encoding='utf-8')):
    if module['file'] not in {'Cmdicon.dll','Itemicon.dll','Mapatr.dll','Mgcicon.dll'}:
        continue
    for index,res in enumerate(module['resources']):
        rows.append({'dll':module['file'],'resource_index':index,
                     'resource_type':str(res['path'][0]),'size':res['size'],
                     'sha256':res['sha256'],'extracted':res['extracted']})
with (root/'analysis/resource-dll-resource-map.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
print(f'Wrote {len(rows)} resource DLL records')
