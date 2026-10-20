"""Measure whether original ITEM pixels reference missing scene-palette entries."""
import json
from pathlib import Path
from collections import Counter
from export_map_layouts import entries
ROOT=Path(__file__).resolve().parents[1]
palettes=list(entries(ROOT/'Spalet.e5'));items=list(entries(ROOT/'Item.e5'))
rows=[];totals=Counter()
for item_id,pixels in items:
    counts=Counter(pixels);totals.update(counts)
    rows.append(dict(itemId=item_id,pixels=len(pixels),maximumIndex=max(counts),visibleIndexes=sorted(index for index in counts if index),tailPixels=sum(count for index,count in counts.items() if index>=246)))
coverage=[]
for index,palette in palettes:
    missing=sorted(color for color in totals if color and color*3+3>len(palette))
    coverage.append(dict(paletteEntry=index,bytes=len(palette),missingUsedIndexes=missing,affectedPixels=sum(totals[color] for color in missing)))
result=dict(scope='exact ITEM.E5 index usage against all Spalet resource lengths; no assumptions about preceding live palette',items=len(rows),pixels=sum(totals.values()),usedIndexes=sorted(totals),rows=rows,palettes=coverage)
text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/item-palette-coverage.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/item-palette-coverage.json').write_text(text,encoding='utf-8')
print(f'ITEM palette audit: {len(rows)} images, {result["pixels"]} pixels; max index {max(totals)}; map31 missing-used {next(row for row in coverage if row["paletteEntry"]==31)["missingUsedIndexes"]}')
