"""Attach verified character/animation link rows to S_00 native units."""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    links={}
    for row in csv.DictReader((ROOT.parent/'caocaozhuan-remake/data/mappings/unit-animation-links.csv').open(encoding='utf-8-sig')):
        links.setdefault(int(row['uid']),row)
    path=ROOT/'analysis/s00-units-readable.json';data=json.loads(path.read_text(encoding='utf-8'))
    for unit in data['units']:
        row=links.get(unit['unitId16'])
        if row:
            unit['animationLink']={k:row[k] for k in ('uid','side','index','class_id','base_sprite','expected','match')}
            unit['animationLinkSource']='unit-animation-links.csv; first side row only'
        else:unit['animationLink']=None
    data['animation_link_matches']=sum(u['animationLink'] is not None for u in data['units'])
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/data/scenarios/S_00-units-native.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Animation-link matches: {data["animation_link_matches"]}/{len(data["units"])}')


if __name__=='__main__':main()
