"""Export exact indexed-darkened movement banks, deduplicated by scene pixel colors."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from export_map_layouts import entries
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT.parent/'caocaozhuan-remake'
corpus=json.loads((ROOT/'analysis/native-palette-lookup-corpus.json').read_text())
units=list(entries(ROOT/'Unit_mov.e5'));used=sorted(set(pixel for _,raw in units for pixel in raw))
profiles={};scenes={};banks=[]
for row in corpus['rows']:
    if not row['name'].startswith('Spalet:'):continue
    scene=int(row['name'].split(':')[1]);palette=row['palette'];lookup=row['lookup'];colors=[]
    for index in range(256):
        target=0 if index==0 else lookup[sum(max(0,palette[index*3+c]-4)*weight for c,weight in enumerate([256,16,1]))]
        colors.append(tuple(palette[target*3+c]*16 for c in [1,2,0])+(255 if target else 0,))
    digest=hashlib.sha256(bytes(value for index in used for value in colors[index])).hexdigest()
    if digest not in profiles:
        profile=len(profiles);profiles[digest]=profile;output=DEST/f'public/assets/animations/acted/profile-{profile}';output.mkdir(parents=True,exist_ok=True)
        rgb=bytes(value for color in colors for value in color[:3]);alpha=bytes(color[3] for color in colors);assets=[]
        for art,raw in units:
            sheet=Image.new('RGBA',(48*11,48))
            for frame in range(11):
                block=raw[frame*2304:(frame+1)*2304];image=Image.frombytes('P',(48,48),block);image.putpalette(rgb);image=image.convert('RGBA');image.putalpha(Image.frombytes('L',(48,48),bytes(alpha[pixel] for pixel in block)));sheet.paste(image,(frame*48,0))
            path=output/f'mov-{art:03d}.png';sheet.save(path);assets.append(dict(art=art,url='/'+path.relative_to(DEST/'public').as_posix()))
        banks.append(dict(profile=profile,representativeScene=scene,colorSha256=digest,assets=assets))
    scenes[str(scene)]=profiles[digest]
result=dict(scope='native darken-by4 and captured per-scene quantization; zero tail controlled; source Unit_mov indices; all scenes deduplicated on used RGBA output',scenes=scenes,banks=banks)
(DEST/'data/mappings/acted-movement-art.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(f'Acted movement art: {len(scenes)} scenes, {len(banks)} distinct pixel profiles, {len(banks)*151} sheets')
