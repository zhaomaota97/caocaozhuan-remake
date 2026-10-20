"""Rebuild battlefield artwork from row-major 48x48 tiles and Spalet palettes."""
import argparse
import json
from pathlib import Path
from PIL import Image
from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()
    output = ROOT / 'analysis/battle-maps'
    output.mkdir(exist_ok=True)
    palettes = dict(entries(ROOT / 'Spalet.e5'))
    manifest = []
    for index, raw in entries(ROOT / 'Hexzmap.e5'):
        width, height = raw[0]//3, raw[1]//3
        artwork = ROOT / f'Hm{index:02d}.e5'
        pixels = artwork.read_bytes()
        if len(pixels) != width*height*48*48:
            raise ValueError(f'{artwork.name}: dimensions disagree with terrain')
        palette = palettes[index]
        if len(palette) % 3 or max(pixels) >= len(palette)//3:
            raise ValueError(f'Palette {index}: missing a used color')
        palette_size = len(palette)
        palette = palette.ljust(768, b'\0')
        record = dict(map_id=index, terrain_entry=index, artwork=artwork.name,
                      palette_file='Spalet.e5', palette_entry=index,
                      width_tiles=width, height_tiles=height,
                      width_pixels=width*48, height_pixels=height*48,
                      artwork_size=len(pixels), palette_bytes=palette_size,
                      max_used_index=max(pixels))
        if args.all or index == 0:
            image = Image.new('P', (width*48,height*48))
            # Native DIB builder 0x40979D maps stored (B,R,G) triples to RGB.
            rgb = bytes(channel & 0xF0 for i in range(0,768,3)
                        for channel in (palette[i+1],palette[i+2],palette[i]))
            image.putpalette(rgb)
            for tile in range(width*height):
                block = Image.frombytes('P',(48,48),pixels[tile*2304:(tile+1)*2304])
                image.paste(block,((tile%width)*48,(tile//width)*48))
            path = output / f'battle-{index:02d}.png'
            image.save(path)
            record['preview'] = path.name
        manifest.append(record)
    (output / 'resource-links.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f'Linked {len(manifest)} terrain/artwork/palette sets; rendered '
          f'{sum("preview" in row for row in manifest)}')


if __name__ == '__main__':
    main()
