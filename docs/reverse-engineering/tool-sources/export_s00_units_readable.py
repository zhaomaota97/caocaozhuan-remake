"""Project only native S_00 record bytes into a conservative readable unit table."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    source=json.loads((ROOT/'analysis/s00-unit-records-native.json').read_text(encoding='utf-8'))
    final=source['snapshots'][-1]
    units=[]
    for record in final['records']:
        b=record['bytes']
        units.append(dict(slot=record['slot'],unitId16=int.from_bytes(bytes(b[0:2]),'little'),
                          rawU32Id=record['u32'][0],
                          coordinateBytes=[b[4],b[5]],
                          controlByte3=b[3],flagsU32=record['u32'][2],
                          classOrLevelByte17=b[17],
                          recordHex=record['raw']))
    result=dict(script='S_00.eex',source_opcode=final['opcode'],source_offset=final['offset'],
                snapshot_scope='after setup opcode72, before scene transition; suspended-process replay, not a full campaign initialized battlefield',
                state_base=source['state_base'],record_size=64,
                count=len(units),units=units,
                field_labels='Only offsets directly observed in 0x4125C5/0x4129A4 are exposed; semantic names remain conservative')
    (ROOT/'analysis/s00-units-readable.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Exported {len(units)} readable S_00 unit records')


if __name__=='__main__':main()
