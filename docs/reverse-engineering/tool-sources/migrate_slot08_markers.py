"""Export verified marker frames and terrain as readable standalone content."""
import csv
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT.parent / 'caocaozhuan-remake'
manifest = json.loads((ROOT / 'analysis/saved-unit-scenes/manifest.json').read_text())
scene = next(x for x in manifest if x['file'] == 'Sv08s.e5s')
mark = (ROOT / 'Mark.e5').read_bytes()
palette = Image.open(ROOT / 'analysis/battle-maps/battle-31.png').getpalette()
atlas = Image.new('RGBA', (48 * 9, 48))
offsets = [0x8bc0 + i * 2304 for i in range(4)] + [0xafc0 + i * 2304 for i in range(2)] + [0x1b5e0 + i * 2304 for i in range(2)] + [0x1ec0]
for frame, offset in enumerate(offsets):
    pixels = mark[offset:offset + 2304]
    tile = Image.frombytes('P', (48, 48), pixels)
    tile.putpalette(palette)
    rgba = tile.convert('RGBA')
    rgba.putalpha(Image.frombytes('L', (48, 48), bytes(255 if value else 0 for value in pixels)))
    atlas.paste(rgba, (frame * 48, 0))
output = DEST / 'public/assets/markers'
output.mkdir(exist_ok=True)
atlas.save(output / 'map31-markers.png')
save_path = DEST / 'data/saves/slot-08.json'
save = json.loads(save_path.read_text(encoding='utf-8'))
main_save = (ROOT / 'Sv08d.e5s').read_bytes()
battle_save = (ROOT / 'Sv08s.e5s').read_bytes()
save['title'] = main_save[0x1b:0x32].split(b'\0', 1)[0].decode('cp936')
save['turn'] = battle_save[35 + 2] + 1
save['turnLimit'] = battle_save[35 + 3]
save['interfaceEvidence'] = {
    'titleOffset': 'Sv08d.e5s + 0x1B',
    'turnOffset': 'Sv08s.e5s + 35 + 2 (display adds one)',
    'turnLimitOffset': 'Sv08s.e5s + 35 + 3',
    'nativeTurnDisplay': ['0x449ECA', '0x47631D'],
}
with (ROOT / 'analysis/characters.csv').open(encoding='utf-8-sig') as file:
    names = {int(row['id']): row['name_gbk'] for row in csv.DictReader(file)}
units = {row['slot']: row['uid'] for row in scene['units']}
for actor in save['actors']:
    uid = units[int(actor['id'].split('-')[1])]
    actor['unitId'] = uid
    actor['name'] = names[uid]
save['markers'] = scene['markers']
save['terrain'] = list((ROOT / 'analysis/saved-battlefields/Sv08s-terrain.bin').read_bytes())
save['markerEvidence'] = {'nativeDraw': '0x452744', 'verifiedFrames': scene['marker_frames_verified'], 'transparentIndex': 0}
save_path.write_text(json.dumps(save, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f"Exported 9 marker frames, {len(scene['markers'])} markers, {len(save['terrain'])} terrain cells")
