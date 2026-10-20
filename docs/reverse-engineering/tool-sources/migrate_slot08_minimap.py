"""Export the actual native Smlmap entry; do not approximate by scaling battlefield art."""
import json
from pathlib import Path
from PIL import Image
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT.parent/'caocaozhuan-remake'
pixels=dict(entries(ROOT/'Smlmap.e5'))[31]
palette=Image.open(ROOT/'analysis/battle-maps/battle-31.png').getpalette()
if len(pixels)!=120*192:
    raise ValueError('Unexpected native minimap size')
image=Image.frombytes('P',(120,192),pixels)
image.putpalette(palette)
output=DEST/'public/assets/maps/minimap-31.png'
image.save(output)
metadata={'mapId':31,'width':120,'height':192,'cellSize':6,'resource':'Smlmap.e5 entry 31',
          'nativeLoad':'0x44A971','nativeUnitOverlay':'0x44A436',
          'unitColorIndices':[42,173,172,172],
          'unitColorMappingStatus':'requires display-palette verification',
          'unitOverlaysConnected':False}
(DEST/'data/mappings/minimap-31.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
print('Exported original minimap-31.png: 120x192; unit overlays not guessed')
