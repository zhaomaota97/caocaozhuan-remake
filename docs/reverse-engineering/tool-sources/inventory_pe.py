"""Inventory shipped PE code and resources without executing modules."""
import hashlib
import json
from pathlib import Path
import pefile
from PIL import Image
from io import BytesIO


def inspect(path):
    pe = pefile.PE(str(path))
    imports = []
    for module in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []):
        imports.append({'dll': module.dll.decode('ascii', errors='replace'),
                        'symbols': [s.name.decode('ascii', errors='replace') if s.name else s.ordinal for s in module.imports]})
    resources = []
    def walk(node, names):
        for item in node.entries:
            key = str(item.name) if item.name is not None else item.id
            if hasattr(item, 'directory'):
                walk(item.directory, names + [key])
            elif hasattr(item, 'data'):
                entry = item.data.struct
                resources.append({'path': names+[key], 'rva': entry.OffsetToData, 'size': entry.Size})
    if hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
        walk(pe.DIRECTORY_ENTRY_RESOURCE, [])
    output = Path('analysis/dll-resources') / path.stem
    output.mkdir(parents=True, exist_ok=True)
    for index, resource in enumerate(resources):
        payload = pe.get_data(resource['rva'], resource['size'])
        target = output / f'{index:04d}.bin'
        target.write_bytes(payload)
        resource['extracted'] = str(target)
        resource['sha256'] = hashlib.sha256(payload).hexdigest()
        if resource['path'][0] == 2:
            try:
                image = Image.open(BytesIO(payload))
                image.load()
                png = target.with_suffix('.png')
                image.save(png)
                resource['image'] = {'path': str(png), 'width': image.width, 'height': image.height}
            except (OSError, ValueError) as error:
                resource['image_error'] = str(error)
    result = {'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'entry_rva': pe.OPTIONAL_HEADER.AddressOfEntryPoint,
              'sections': [{'name': s.Name.rstrip(b'\0').decode(), 'size': s.SizeOfRawData,
                            'executable': bool(s.Characteristics & 0x20000000)} for s in pe.sections],
              'imports': imports, 'resources': resources,
              'exports': [{'name': s.name.decode() if s.name else None, 'rva': s.address}
                          for s in getattr(getattr(pe, 'DIRECTORY_ENTRY_EXPORT', None), 'symbols', [])]}
    pe.close()
    return result


if __name__ == '__main__':
    rows = [inspect(p) for p in sorted(Path('.').glob('*.dll'))]
    Path('analysis/dll-inventory.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    for row in rows:
        print(row['file'], 'entry', hex(row['entry_rva']), 'resources', len(row['resources']),
              'imports', len(row['imports']), 'exports', len(row['exports']),
              'code_bytes', sum(s['size'] for s in row['sections'] if s['executable']))
