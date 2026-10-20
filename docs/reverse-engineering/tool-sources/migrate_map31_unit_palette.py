"""Export unit sheets with the actual map-31 palette and indexed transparency."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT.parent / 'caocaozhuan-remake'
palette = dict(entries(ROOT / 'Spalet.e5'))[31].ljust(768, b'\0')
rgb = bytes(channel & 0xf0 for i in range(0, 768, 3)
            for channel in (palette[i+1], palette[i+2], palette[i]))
output = DEST / 'public/assets/animations/movement-map31'
output.mkdir(parents=True, exist_ok=True)
records = []
for index, raw in entries(ROOT / 'Unit_mov.e5'):
    if len(raw) != 11 * 2304:
        raise ValueError(f'Unexpected movement resource length: {index}')
    sheet = Image.new('RGBA', (528, 48))
    for frame in range(11):
        pixels = raw[frame * 2304:(frame + 1) * 2304]
        tile = Image.frombytes('P', (48, 48), pixels)
        tile.putpalette(rgb)
        rgba = tile.convert('RGBA')
        rgba.putalpha(Image.frombytes('L', (48, 48), bytes(255 if p else 0 for p in pixels)))
        sheet.paste(rgba, (frame * 48, 0))
    path = output / f'mov-{index:03d}.png'
    sheet.save(path)
    records.append({'index': index, 'paletteMap': 31, 'transparentIndex': 0,
                    'url': '/' + path.relative_to(DEST / 'public').as_posix(),
                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
(DEST / 'data/mappings/unit-sheets-map31.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
print(f'Exported {len(records)} map-31 unit sheets; alpha is derived from palette index 0 only')
