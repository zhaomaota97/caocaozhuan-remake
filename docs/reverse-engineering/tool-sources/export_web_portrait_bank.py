"""Export FACE index pixels and scene palettes without fixing a global palette."""
import argparse
import base64
import json
from pathlib import Path

from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    faces = []
    for index, pixels in entries(ROOT / 'Face.e5'):
        if len(pixels) != 64 * 80:
            raise ValueError(f'Invalid FACE entry {index}: {len(pixels)}')
        faces.append({'index': index, 'pixelsBase64': base64.b64encode(pixels).decode('ascii')})
    palettes = []
    for filename in ('Pmpalet.e5', 'Spalet.e5'):
        for index, raw in entries(ROOT / filename):
            palettes.append({'file': filename, 'index': index,
                             'nativeBgrBase64': base64.b64encode(raw).decode('ascii')})
    result = {'width': 64, 'height': 80, 'transparentIndex': 0,
              'selector': '0x4075A7', 'blit': '0x47F740',
              'paletteUpload': '0x47E867',
              'channelOrder': 'stored B,R,G; RGB output uses bytes 1,2,0 masked with 0xF0',
              'scope': 'Resource bank only; dialogue geometry and active palette timing require integration.',
              'faces': faces, 'palettes': palettes}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    print(f'Exported {len(faces)} faces and {len(palettes)} palettes to {args.output}')


if __name__ == '__main__':
    main()
