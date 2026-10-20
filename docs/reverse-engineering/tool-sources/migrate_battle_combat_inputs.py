"""Export verified slot-08 combat attributes and native attack/special sprite banks."""
import json
from pathlib import Path
from PIL import Image
from export_map_layouts import entries
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT.parent/'caocaozhuan-remake'
evidence=json.loads((ROOT/'analysis/native-saved-ordinary-damage.json').read_text(encoding='utf-8'))
actors=[{key:a[key] for key in ('slot','attack','defense','agility','luck','nativeLevel','classId','hp','mp','actorFlags','statusFlags')} for a in evidence['actors']]
(DEST/'data/mappings/slot08-combat-runtime.json').write_text(json.dumps({'scope':'Verified native getter snapshots; equipment/stat growth requires recalculation','actors':actors},indent=2)+'\n',encoding='utf-8')
palette=dict(entries(ROOT/'Spalet.e5'))[31].ljust(768,b'\0')
rgb=bytes(v&0xf0 for i in range(0,768,3) for v in (palette[i+1],palette[i+2],palette[i]))
manifest=[]
for family,side,count in [('atk',64,12),('spc',48,5)]:
 output=DEST/f'public/assets/animations/{family}-map31';output.mkdir(parents=True,exist_ok=True)
 for index,raw in entries(ROOT/f'Unit_{family}.e5'):
  assert len(raw)==side*side*count
  sheet=Image.new('RGBA',(side*count,side))
  for frame in range(count):
   pixels=raw[frame*side*side:(frame+1)*side*side];tile=Image.frombytes('P',(side,side),pixels);tile.putpalette(rgb);rgba=tile.convert('RGBA')
   rgba.putalpha(Image.frombytes('L',(side,side),bytes(255 if p else 0 for p in pixels)));sheet.paste(rgba,(frame*side,0))
  path=output/f'{family}-{index:03d}.png';sheet.save(path)
  manifest.append({'family':family,'index':index,'tileSize':side,'frames':count,'url':'/'+path.relative_to(DEST/'public').as_posix()})
(DEST/'data/mappings/combat-sheets-map31.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(f'Exported {len(actors)} native combat snapshots and {len(manifest)} map31 combat sheets')
