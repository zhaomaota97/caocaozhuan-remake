"""Attach character-table names and raw character records to S_00 native units."""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    characters={int(row['id']):row for row in csv.DictReader((ROOT/'analysis/characters.csv').open(encoding='utf-8-sig'))}
    data=json.loads((ROOT/'analysis/s00-units-readable.json').read_text(encoding='utf-8'))
    for unit in data['units']:
        row=characters.get(unit['unitId16'])
        if row:
            unit['characterName']=row['name_gbk']
            unit['characterRecordHex']=row['record_hex'].replace(' ','')
            unit['characterTableMatch']=True
        else:
            unit['characterName']=None;unit['characterRecordHex']=None;unit['characterTableMatch']=False
    data['character_table']='analysis/characters.csv';data['field_labels']+='; characterName is a direct character-table ID match, not a semantic class inference'
    (ROOT/'analysis/s00-units-readable.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    dest=ROOT.parent/'caocaozhuan-remake/data/scenarios/S_00-units-native.json'
    dest.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Character-table matches: {sum(u["characterTableMatch"] for u in data["units"])}/{len(data["units"])}')


if __name__=='__main__':main()
