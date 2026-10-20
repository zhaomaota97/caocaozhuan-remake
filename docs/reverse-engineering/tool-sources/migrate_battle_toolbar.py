"""Recover bitmap 302 and the original 32-bit TBBUTTON array at 0x48EA78."""
import io
import json
import struct
from pathlib import Path
import pefile
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT.parent / 'caocaozhuan-remake'
pe = pefile.PE(str(ROOT / 'Ekd5.exe'))
menus = next(t for t in pe.DIRECTORY_ENTRY_RESOURCE.entries if t.id == 4)
menu_leaf = menus.directory.entries[0].directory.entries[0].data.struct
menu_raw = pe.get_data(menu_leaf.OffsetToData, menu_leaf.Size)
menu_version, menu_offset = struct.unpack_from('<HH', menu_raw)
if menu_version != 0:
    raise ValueError('Unsupported menu resource version')
labels = {}
def read_menu(position):
    while True:
        flags = struct.unpack_from('<H', menu_raw, position)[0]
        position += 2
        command = None
        if not flags & 0x10:
            command = struct.unpack_from('<H', menu_raw, position)[0]
            position += 2
        end = position
        while menu_raw[end:end + 2] != b'\0\0':
            end += 2
        title = menu_raw[position:end].decode('utf-16le')
        position = end + 2
        if command:
            labels[command] = title
        if flags & 0x10:
            position = read_menu(position)
        if flags & 0x80:
            return position
read_menu(4 + menu_offset)
resource = next(t for t in pe.DIRECTORY_ENTRY_RESOURCE.entries if t.id == 2)
entry = next(e for e in resource.directory.entries if e.id == 302)
leaf = entry.directory.entries[0].data.struct
dib = pe.get_data(leaf.OffsetToData, leaf.Size)
header_size = struct.unpack_from('<I', dib)[0]
bits = struct.unpack_from('<H', dib, 14)[0]
colors = struct.unpack_from('<I', dib, 32)[0] or (1 << bits if bits <= 8 else 0)
header = b'BM' + struct.pack('<IHHI', 14 + len(dib), 0, 0, 14 + header_size + colors * 4)
image = Image.open(io.BytesIO(header + dib)).convert('RGBA')
directory = DEST / 'public/assets/ui/battle-toolbar'
directory.mkdir(parents=True, exist_ok=True)
image.save(directory / 'strip.png')
raw = pe.get_data(0x8ea78, 15 * 20)
buttons = []
for i in range(15):
    bitmap, command, state, style = struct.unpack_from('<iiBB', raw, i * 20)
    row = {'order': i, 'commandId': command, 'bitmapIndex': bitmap, 'separator': bool(style & 1), 'nativeState': state}
    if not row['separator']:
        row['label'] = labels.get(command)
        tile = image.crop((bitmap * 24, 0, (bitmap + 1) * 24, 24))
        tile.save(directory / f'command-{command}.png')
        row['url'] = f'/assets/ui/battle-toolbar/command-{command}.png'
    buttons.append(row)
result = {'bitmapResource': 302, 'buttonTable': '0x48EA78', 'createFunction': '0x476063',
          'width': 24, 'height': 24, 'stripSize': list(image.size), 'buttons': buttons}
(DEST / 'data/mappings/battle-toolbar.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(f'Toolbar bitmap {image.size}, {len(buttons)} native button records exported')
