"""Compare all unit-animation visible palette indexes across battle palettes."""
import hashlib
import json
from collections import Counter
from pathlib import Path
from export_map_layouts import entries
ROOT=Path(__file__).resolve().parents[1]
palettes=dict(entries(ROOT/'Spalet.e5'));baseline=palettes[31];families=[]
for family in ['atk','mov','spc']:
    resources=[];totals=Counter()
    for index,pixels in entries(ROOT/f'Unit_{family}.e5'):
        counts=Counter(pixels);totals.update(counts);resources.append(dict(index=index,pixels=len(pixels),counts=counts))
    used=sorted(index for index in totals if index);profiles={};rows=[]
    for scene,palette in palettes.items():
        missing=sorted(index for index in used if index*3+3>len(palette))
        changed=sorted(index for index in used if index not in missing and bytes(v&240 for v in palette[index*3:index*3+3])!=bytes(v&240 for v in baseline[index*3:index*3+3]))
        colors=bytes(value&240 for index in used if index not in missing for value in palette[index*3:index*3+3]);digest=hashlib.sha256(colors).hexdigest()
        if digest not in profiles:profiles[digest]=len(profiles)
        affected=[dict(index=row['index'],changedPixels=sum(row['counts'].get(index,0) for index in changed+missing)) for row in resources if any(index in row['counts'] for index in changed+missing)]
        rows.append(dict(paletteEntry=scene,profile=profiles[digest],visibleColorSha256=digest,missingUsedIndexes=missing,changedIndexesFrom31=changed,affectedResources=affected))
    families.append(dict(family=family,resources=len(resources),pixels=sum(totals.values()),usedIndexes=used,colorProfiles=len(profiles),rows=rows))
result=dict(scope='exhaustive original unit indexed-pixel and Spalet high-nibble comparison; not animation ordering, background blending or live palette transitions',families=families)
text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/unit-scene-colors.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/unit-scene-colors.json').write_text(text,encoding='utf-8')
for family in families:print(f'{family["family"]}: {family["resources"]} resources, {family["pixels"]} pixels, {family["colorProfiles"]} profiles, {sum(bool(row["affectedResources"]) for row in family["rows"])} affected palettes')
