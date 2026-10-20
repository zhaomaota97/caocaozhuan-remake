"""Recover treasure membership from native item record +0x18."""
import csv
import json
from pathlib import Path
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT.parent/'caocaozhuan-remake/data/mappings/treasure-catalog.json'
raw=dict(entries(ROOT/'Data.e5'))[1]
classes=dict(entries(ROOT/'Data.e5'))[3]
with (ROOT/'analysis/items.csv').open(encoding='utf-8-sig') as stream:
    items={int(row['id']):row for row in csv.DictReader(stream)}
rows=[]
flags=(ROOT/'Svcmn.e5s').read_bytes()
with (ROOT/'analysis/imsg.csv').open(encoding='utf-8-sig') as stream:
    descriptions={int(row['id']):row for row in csv.DictReader(stream)}
for item_id in range(104):
    record=bytes.fromhex(items[item_id]['runtime_hex'])
    if record[24]:
        allowed=[]
        for group in range(13):
            class_id=group*3
            category=record[17]
            allowed.append(bool(classes[class_id*27+9+category]) if category<18
                           else record[23] in (group,255))
        rows.append({'number':len(rows)+1,'itemId':item_id,'name':items[item_id]['name'],
                     'equipGroups':allowed,
                     'membershipByte':record[24], 'discoveryFlagIndex':item_id+3,
                     'discovered':flags[item_id+3]!=0,
                     'iconIndex':record[19],
                     'iconResourceId':101+record[19]*2,
                     'iconUrl':f'/assets/ui/dll/itemicon/{record[19]*2+1:04d}.png',
                     'categoryLabel':items[item_id]['category_label'],
                     'price':None if record[18]==255 else record[18]*100,
                     'description':next((v for k,v in descriptions.get(item_id,{}).items() if k not in ('id','raw_hex') and not k.endswith('hex')), '')})
out={'evidence':{'membership':'0x409600','populate':'0x47072D','discovery':'0x470664 -> 0x41A284'},
     'dialogResource':333,'listResource':347,'entryResource':334,
     'columns':3,'visibleRows':6,'entries':rows}
DEST.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Exported {len(rows)} treasure records; grid=3x6; discovery flags remain separate')
