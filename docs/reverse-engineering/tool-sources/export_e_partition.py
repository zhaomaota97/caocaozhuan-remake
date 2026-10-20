"""Decode the byte layout written by native E-partition reader 0x417A54."""
import json,struct,sys
from pathlib import Path

if len(sys.argv)!=2:
    raise SystemExit('usage: export_e_partition.py <Sv??E.e5s>')
path=Path(sys.argv[1]); raw=path.read_bytes(); pos=0
def take(size):
    global pos
    value=raw[pos:pos+size];pos+=size
    if len(value)!=size: raise ValueError(f'truncated at 0x{pos-size:X}')
    return value
def u8(): return take(1)[0]
def u16(): return struct.unpack('<H',take(2))[0]
def u32(): return struct.unpack('<I',take(4))[0]
records=[]
for index in range(0x73):
    records.append({'index':index,'word0':u32(),'byte4':u8(),'byte5':u8(),
                    'word6':u32(),'byte10':u8(),'word11':u16(),'byte13':u8(),'byte14':u8()})
block181=take(0x181); byte3d0e=u8(); byte3d0f=u8(); block3d04=take(8)
values=[u32() for _ in range(0x800)]
tail2038=u32(); tail203c=u32(); aux=take(10)
if pos!=len(raw): raise ValueError(f'{len(raw)-pos} trailing bytes at 0x{pos:X}')
auxValues=list(struct.unpack('<5H',aux))
result={'file':path.name,'bytes':len(raw),'versionByte':raw[0],
 'records':records,'block3d10':block181.hex(),'byte3d0e':byte3d0e,'byte3d0f':byte3d0f,
 'block3d04':block3d04.hex(),'values2038':values,'tail2038':tail2038,'tail203c':tail203c,
 'aux10':aux.hex(),'auxUint16':auxValues,
 'auxFieldOffsets':['object+0x04','object+0x08','object+0x10','object+0x14','object+0x24'],
 'auxEvidenceRead':'0x410506','auxEvidenceWrite':'0x410470',
 'evidenceFunction':'0x417A54','serializedRecordBytes':15}
out=path.with_suffix(path.suffix+'.json')
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'{path.name}: decoded {len(records)} records, 0x800 values, {pos} bytes -> {out}')
