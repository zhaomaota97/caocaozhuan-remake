"""Compare visible ITEM colors across every scene palette without tail assumptions."""
import hashlib
import json
from pathlib import Path
from export_map_layouts import entries
ROOT=Path(__file__).resolve().parents[1]
items=list(entries(ROOT/'Item.e5'));palettes=dict(entries(ROOT/'Spalet.e5'))
used=sorted(set(value for _,pixels in items for value in pixels if value))
baseline=palettes[31];rows=[];profiles={}
for scene,palette in palettes.items():
    if any(index*3+3>len(palette) for index in used):raise RuntimeError(f'Missing visible source colors in palette {scene}')
    colors=bytes(value&240 for index in used for value in palette[index*3:index*3+3])
    digest=hashlib.sha256(colors).hexdigest()
    if digest not in profiles:profiles[digest]=len(profiles)
    changed=[index for index in used if bytes(v&240 for v in palette[index*3:index*3+3])!=bytes(v&240 for v in baseline[index*3:index*3+3])]
    affected=[dict(itemId=item,changedPixels=sum(pixel in changed for pixel in pixels)) for item,pixels in items if any(pixel in changed for pixel in pixels)]
    rows.append(dict(paletteEntry=scene,colorProfile=profiles[digest],visibleColorSha256=digest,changedIndexesFrom31=changed,affectedItems=affected))
result=dict(scope='all nontransparent ITEM source colors across all 58 Spalet records; high-nibble comparison; no background or blend quantization claim',items=len(items),usedIndexes=used,palettes=len(rows),colorProfiles=len(profiles),rows=rows)
text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/item-scene-colors.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/item-scene-colors.json').write_text(text,encoding='utf-8')
print(f'ITEM scene colors: {len(rows)} palettes, {len(profiles)} visible color profiles, {sum(bool(r["affectedItems"]) for r in rows)} differ from map31')
