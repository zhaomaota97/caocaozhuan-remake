"""Export original roster column labels from 0x47A3CC."""
import json
import struct
from pathlib import Path
import pefile
ROOT=Path(__file__).resolve().parents[1]
pe=pefile.PE(str(ROOT/'Ekd5.exe'))
addresses=[0x486ab0,0x486ab8,0x486ac4,0x486ad0,0x486ad8,0x486adc,0x486ae8,0x486af8,0x486b08,0x486b18,struct.unpack('<I',pe.get_data(0x86b28,4))[0]]
rows=[{'id':i,'label':pe.get_data(a-0x400000,64).split(b'\0')[0].decode('cp936'),'sourceAddress':hex(a)} for i,a in enumerate(addresses)]
out={'dialogResource':186,'listControlId':1026,'populate':'0x47A3CC','sort':'0x479F91','factionSwitch':'0x47AE51','columns':rows}
(ROOT.parent/'caocaozhuan-remake/data/mappings/roster-columns.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Exported {len(rows)} original roster column labels')
