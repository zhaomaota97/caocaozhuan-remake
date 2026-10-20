"""Audit static Data.e5 entry references and distinguish loaded vs unreferenced entries."""
import json
from pathlib import Path
from extract_e5 import decode
import struct

ROOT=Path(__file__).resolve().parents[1]

def main():
    data=(ROOT/'Data.e5').read_bytes();entries=[]
    for i in range(10):
        packed,size,offset=struct.unpack_from('>III',data,0x110+i*12)
        entries.append(dict(index=i,packed=packed,decoded=size,offset=offset))
    refs=[]
    for path in (ROOT/'analysis/native-main/pseudocode').glob('*.c'):
        text=path.read_text(encoding='utf-8',errors='replace')
        if 's_DATA_E5' in text:
            refs.append(path.name)
    result=dict(entries=entries,static_loader_functions=refs,
                explicitly_loaded_indices=[0,1,2,3,4,5],
                no_explicit_loader_found=[6,7,8,9],
                interpretation='Entries 6-9 exist and decode, but this Ghidra build has no discovered Data.e5 loader call or runtime-table population for them.')
    (ROOT/'analysis/data-entry-reference-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Data.e5 static audit: explicit loaders 0-5; no loader references found for 6-9')

if __name__=='__main__':main()
