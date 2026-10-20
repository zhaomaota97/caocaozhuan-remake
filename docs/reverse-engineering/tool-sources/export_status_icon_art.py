"""Extract original raw MARK status sprites at native renderer offsets."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from export_map_layouts import entries
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT.parent/'caocaozhuan-remake'
raw=(ROOT/'Mark.e5').read_bytes();assert len(raw)==0x1c7e0
palettes=dict(entries(ROOT/'Spalet.e5'));palette=palettes[31].ljust(768,b'\0');rgb=bytes(v&240 for i in range(0,768,3) for v in [palette[i+1],palette[i+2],palette[i]])
output=DEST/'public/assets/markers/status';output.mkdir(parents=True,exist_ok=True);rows=[]
for offset in [0x1a2c0,0x1a3c0,0x1a4c0]:
    pixels=raw[offset:offset+256];used=sorted(set(pixels)-{0})
    for scene,colors in palettes.items():
        if any(bytes(v&240 for v in colors[index*3:index*3+3])!=bytes(v&240 for v in palette[index*3:index*3+3]) for index in used):raise RuntimeError(f'Scene {scene}: status icon palette varies')
    image=Image.frombytes('P',(16,16),pixels);image.putpalette(rgb);image=image.convert('RGBA');image.putalpha(Image.frombytes('L',(16,16),bytes(255 if index else 0 for index in pixels)))
    path=output/f'{offset:x}.png';image.save(path)
    rows.append(dict(offset=offset,width=16,height=16,url='/'+path.relative_to(DEST/'public').as_posix(),sha256=hashlib.sha256(pixels).hexdigest(),usedIndexes=used))
result=dict(source='Mark.e5',nativeLoader='0x42BA29',sourceBytes=len(raw),paletteEntry=31,identicalSourceColorsAcross58Palettes=True,rows=rows)
(DEST/'data/mappings/status-icon-art.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('Exported three original MARK status icons; source colors match all 58 palettes')
