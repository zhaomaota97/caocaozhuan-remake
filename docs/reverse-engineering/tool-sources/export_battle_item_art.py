"""Export every ITEM.E5 image using the verified map31 palette conversion."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT.parent/'caocaozhuan-remake'
output=DEST/'public/assets/effects/items-map31';output.mkdir(parents=True,exist_ok=True)
palette=dict(entries(ROOT/'Spalet.e5'))[31].ljust(768,b'\0')
rgb=bytes(v&0xf0 for i in range(0,768,3) for v in (palette[i+1],palette[i+2],palette[i]))
rows=[]
for index,raw in entries(ROOT/'Item.e5'):
    if len(raw)!=1024:raise ValueError(f'ITEM entry {index}: {len(raw)} bytes, expected 1024')
    image=Image.frombytes('P',(32,32),raw);image.putpalette(rgb);image=image.convert('RGBA')
    image.putalpha(Image.frombytes('L',(32,32),bytes(255 if pixel else 0 for pixel in raw)))
    path=output/f'item-{index:03d}.png';image.save(path)
    pixels=Image.open(path).convert('RGBA')
    expected=bytes(component for pixel in raw for component in (*rgb[pixel*3:pixel*3+3],255 if pixel else 0))
    if pixels.tobytes()!=expected:raise ValueError(f'ITEM entry {index}: PNG round-trip mismatch')
    rows.append(dict(itemId=index,width=32,height=32,url='/'+path.relative_to(DEST/'public').as_posix(),indexSha256=hashlib.sha256(raw).hexdigest(),rgbaSha256=hashlib.sha256(expected).hexdigest()))
report=dict(scope='all ITEM.E5 entries, map31 palette only; original indexed art, zero-index transparency; not all campaign palette timing',paletteEntry=31,rows=rows)
(DEST/'data/mappings/battle-item-art.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(f'Battle item images exported and pixel-verified: {len(rows)}')
