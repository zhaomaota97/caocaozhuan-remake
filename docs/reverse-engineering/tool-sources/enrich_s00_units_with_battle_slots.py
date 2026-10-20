"""Apply the native 0x44CC85 slot-group allocation to S_00 records."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    path=ROOT/'analysis/s00-units-readable.json';data=json.loads(path.read_text(encoding='utf-8'))
    counters={0:0,2:15,'other':35}
    groups={0:'primary-slot-group',2:'auxiliary-slot-group','other':'enemy-slot-group'}
    for unit in sorted(data['units'],key=lambda x:x['slot']):
        key=unit['flagsU32']&3
        group=key if key in (0,2) else 'other'
        unit['nativeSlotGroup']=groups[group]
        unit['nativeBattleSlot']=counters[group]
        counters[group]+=1
        unit['flagsLow2']=key
    data['battle_slot_allocator']={'function':'0x44CC85','rules':{
        'flags&3==0':'slots begin at 0','flags&3==2':'slots begin at 15','otherwise':'slots begin at 35'},
        'note':'group names describe native slot ranges; they are not invented UI faction labels'}
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/data/scenarios/S_00-units-native.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print('S_00 native battle slots:',[(u['characterName'],u['nativeBattleSlot'],u['nativeSlotGroup']) for u in data['units']])


if __name__=='__main__':main()
