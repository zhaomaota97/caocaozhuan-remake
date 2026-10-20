"""Decode raw unit records captured from the S_00 native setup replay."""
import json
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def decode(raw):
    records=[]
    base=0x2044
    for slot in range(0x73):
        off=base+slot*0x40
        blob=bytes(raw[off:off+0x40])
        if len(blob)!=0x40:break
        unit_id=struct.unpack_from('<I',blob,0)[0]
        if struct.unpack_from('<H',blob,0)[0] == 0xFFFF:continue
        records.append(dict(slot=slot,offset=off,unit_id=unit_id,
                            raw=blob.hex(),
                            u32=[struct.unpack_from('<I',blob,i)[0] for i in range(0,0x40,4)],
                            bytes=list(blob)))
    return records


def main():
    source=json.loads((ROOT/'analysis/native-s00-unit-setup-replay.json').read_text(encoding='utf-8'))
    rows=[]
    for event in source['rows']:
        if event.get('state_after'):
            rows.append(dict(opcode=event['opcode'],offset=event['offset'],records=decode(event['state_after'])))
    result=dict(script='S_00.eex',state_base='0x492F90+0x2044',record_size=64,record_count=115,
                final_snapshot={'opcode':rows[-1]['opcode'],'offset':rows[-1]['offset']},
                snapshots=rows,scope='raw native records; field labels intentionally omitted pending full unit schema')
    (ROOT/'analysis/s00-unit-records-native.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('S_00 snapshots:',[(r['opcode'],len(r['records'])) for r in rows])


if __name__=='__main__':main()
