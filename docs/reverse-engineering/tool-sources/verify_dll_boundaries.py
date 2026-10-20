#!/usr/bin/env python3
import json,hashlib,pefile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
d={x['file']:x for x in json.loads((root/'analysis/dll-inventory.json').read_text(encoding='utf-8'))}
resource=['Cmdicon.dll','Itemicon.dll','Mapatr.dll','Mgcicon.dll']
hashes=[]
for n in resource:
 pe=pefile.PE(str(root/n)); sec=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text'); hashes.append(hashlib.sha256(sec.get_data()).hexdigest())
checks={'resource_text_hashes_equal':len(set(hashes))==1,
        'autodll_asave_export':any(x.get('name')=='ASave' for x in d['AutoDLL.dll']['exports']),
        'koeicda_export_count':len(d['Koeicda.dll']['exports'])==20}
for k,v in checks.items(): print(f'{k}: {"PASS" if v else "FAIL"}')
print('resource_hash',hashes[0])
if not all(checks.values()): raise SystemExit(1)
