"""Export PE imports, exports, sections and executable/resource characteristics."""
import json
from pathlib import Path
import pefile

ROOT=Path(__file__).resolve().parents[1]
targets=[ROOT/'Ekd5.exe']+sorted(ROOT.glob('*.dll'))
rows=[]
for path in targets:
    pe=pefile.PE(str(path),fast_load=False)
    exports=[]
    if hasattr(pe,'DIRECTORY_ENTRY_EXPORT'):
        for symbol in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            exports.append({'ordinal':symbol.ordinal,'name':symbol.name.decode(errors='replace') if symbol.name else None,
                            'rva':symbol.address})
    imports=[]
    if hasattr(pe,'DIRECTORY_ENTRY_IMPORT'):
        for descriptor in pe.DIRECTORY_ENTRY_IMPORT:
            dll=descriptor.dll.decode(errors='replace')
            imports.append({'dll':dll,'symbols':[entry.name.decode(errors='replace') if entry.name else f'ordinal:{entry.ordinal}'
                                                  for entry in descriptor.imports]})
    sections=[]
    for section in pe.sections:
        name=section.Name.rstrip(b'\0').decode(errors='replace')
        characteristics=section.Characteristics
        sections.append({'name':name,'virtualAddress':section.VirtualAddress,'virtualSize':section.Misc_VirtualSize,
                         'rawSize':section.SizeOfRawData,'executable':bool(characteristics&0x20000000),
                         'writable':bool(characteristics&0x80000000),'readable':bool(characteristics&0x40000000)})
    rows.append({'file':path.name,'size':path.stat().st_size,'machine':pe.FILE_HEADER.Machine,
                 'timestamp':pe.FILE_HEADER.TimeDateStamp,'entryRva':pe.OPTIONAL_HEADER.AddressOfEntryPoint,
                 'exports':exports,'imports':imports,'sections':sections,
                 'hasResourceDirectory':bool(pe.OPTIONAL_HEADER.DATA_DIRECTORY[2].VirtualAddress)})
    pe.close()
(ROOT/'analysis/pe-dependency-inventory.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'PE dependency inventory: {len(rows)} files, {sum(len(r["exports"]) for r in rows)} exports, {sum(len(r["imports"]) for r in rows)} import DLL groups')
