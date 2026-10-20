"""Copy decoded DLL images without filename collisions, recording local URLs and hashes."""
import hashlib
import json
import shutil
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT.parent / 'caocaozhuan-remake'
rows = []
for module in ('Cmdicon', 'Itemicon', 'Mapatr', 'Mgcicon'):
    source = ROOT / 'analysis/dll-resources' / module
    target = DEST / 'public/assets/ui/dll' / module.lower()
    target.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.glob('*.png')):
        output = target / path.name
        shutil.copy2(path, output)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if hashlib.sha256(output.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Hash mismatch: {output}')
        indexed = Image.open(output)
        image = indexed.convert('RGBA')
        if indexed.mode == 'P':
            indices = list(indexed.getdata())
            image.putalpha(Image.frombytes('L',image.size,bytes(0 if i==0 else 255 for i in indices)))
        else:
            image.putdata([(r,g,b,0 if (r,g,b)==(255,0,255) else a)
                           for r,g,b,a in image.getdata()])
        image.save(output)
        output_digest = hashlib.sha256(output.read_bytes()).hexdigest()
        rows.append({'module': module, 'resourceIndex': int(path.stem),
                     'url': '/' + output.relative_to(DEST / 'public').as_posix(),
                     'sourceSha256': digest, 'sha256': output_digest,
                     'transparentIndex': 0, 'maskEvidence': '0x40A58A(this, 0)'})
if len(rows) != 304:
    raise ValueError(f'Expected 304 decoded images, found {len(rows)}')
manifest = DEST / 'data/mappings/dll-image-assets.json'
manifest.write_text(json.dumps(rows, indent=2) + '\n', encoding='utf-8')
print(f'Copied and hash-verified {len(rows)} images in four separate module directories')
