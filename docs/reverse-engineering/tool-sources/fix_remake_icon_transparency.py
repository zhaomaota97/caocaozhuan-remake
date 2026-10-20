"""Apply the native 0x4613F3 magenta color key to copied UI icons."""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1].parent / 'caocaozhuan-remake/public/assets/ui'
changed = 0
pixels = 0
for path in sorted(root.rglob('*.png')):
    image = Image.open(path).convert('RGBA')
    data = list(image.getdata())
    count = sum(r == 255 and g == 0 and b == 255 and a != 0 for r, g, b, a in data)
    if not count:
        continue
    image.putdata([(r, g, b, 0 if (r, g, b) == (255, 0, 255) else a) for r, g, b, a in data])
    image.save(path)
    changed += 1
    pixels += count
print(f'Applied native magenta key: {changed} PNG files, {pixels} pixels')
