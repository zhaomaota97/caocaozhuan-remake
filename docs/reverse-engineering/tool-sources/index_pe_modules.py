"""Index native modules, PE metadata, imports/exports and pseudocode coverage."""
from pathlib import Path
import json
import re
import pefile

ROOT=Path(__file__).resolve().parents[1]
runtime=ROOT/'analysis/runtime-game'
modules=[]
for path in sorted(runtime.glob('*')):
    if path.suffix.lower() not in ('.exe','.dll'):
        continue
    pe=pefile.PE(str(path),fast_load=False)
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'],pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT']])
    imports=[]
    for entry in getattr(pe,'DIRECTORY_ENTRY_IMPORT',[]):
        names=[]
        for imp in entry.imports:
            names.append({'name':imp.name.decode('ascii','replace') if imp.name else None,'ordinal':imp.ordinal,'address':hex(imp.address)})
        imports.append({'dll':entry.dll.decode('ascii','replace'),'symbols':names})
    exports=[]
    if hasattr(pe,'DIRECTORY_ENTRY_EXPORT'):
        exports=[{'name':e.name.decode('ascii','replace') if e.name else None,'ordinal':e.ordinal,'rva':hex(e.address)} for e in pe.DIRECTORY_ENTRY_EXPORT.symbols]
    sections=[{'name':s.Name.rstrip(b'\\0').decode('ascii','replace'),'rva':hex(s.VirtualAddress),'virtualSize':s.Misc_VirtualSize,'rawSize':s.SizeOfRawData,'characteristics':hex(s.Characteristics)} for s in pe.sections]
    modules.append({'file':path.name,'size':path.stat().st_size,'machine':hex(pe.FILE_HEADER.Machine),'timestamp':pe.FILE_HEADER.TimeDateStamp,'entryRva':hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint),'imageBase':hex(pe.OPTIONAL_HEADER.ImageBase),'sections':sections,'imports':imports,'exports':exports})
coverage=[]
for p in sorted((ROOT/'analysis/native-main/pseudocode').glob('*.c')):
    m=re.search(r'([0-9a-fA-F]{8})',p.name)
    coverage.append({'file':p.name,'address':'0x'+m.group(1).lower() if m else None})
out={'scope':'analysis/runtime-game','modules':modules,'pseudocodeFiles':coverage,'pseudocodeCount':len(coverage)}
(ROOT/'analysis/native-module-index.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
lines=['# Native module index','',f'Modules: {len(modules)}. Ghidra pseudocode files: {len(coverage)}.','', '| Module | Size | Imports | Exports | Entry RVA |','|---|---:|---:|---:|---|']
for m in modules:lines.append(f"| `{m['file']}` | {m['size']} | {sum(len(i['symbols']) for i in m['imports'])} | {len(m['exports'])} | `{m['entryRva']}` |")
lines += ['', '## Module details', '']
for m in modules:
    lines += [f"### `{m['file']}`",'',f"PE machine `{m['machine']}`, image base `{m['imageBase']}`, timestamp `{m['timestamp']}`.",'', 'Imports:']
    for i in m['imports']:lines.append(f"- `{i['dll']}`: {len(i['symbols'])} symbols")
    lines += ['', 'Sections:']
    for s in m['sections']:lines.append(f"- `{s['name']}` RVA `{s['rva']}`, virtual {s['virtualSize']}, raw {s['rawSize']}")
    if m['exports']:lines += ['', 'Exports:']+[f"- `{e['name'] or '(ordinal)'}` ordinal {e['ordinal']} RVA `{e['rva']}`" for e in m['exports']]
(ROOT/'analysis/native-module-index.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(f'Indexed {len(modules)} modules; {len(coverage)} pseudocode files')
