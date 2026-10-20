"""Keep controlled native expansion separate from raw scenario records."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    path=ROOT/'analysis/s00-units-readable.json'
    data=json.loads(path.read_text(encoding='utf-8'))
    expanded=json.loads((ROOT/'analysis/native-s00-expanded-units.json').read_text(encoding='utf-8'))
    lookup={u['unitId']:u for u in expanded['units']}
    changed=[]
    for unit in data['units']:
        native=lookup[unit['unitId16']]
        unit['controlledNativeExpansion']=native
        previous=int(unit['animationLink']['index'])
        if previous!=native['art']:
            changed.append(dict(unitId=native['unitId'],name=unit['characterName'],
                                previousArt=previous,nativeArt=native['art']))
    data['controlled_expansion_scope']=expanded['scope']
    data['animation_first_side_differences']=changed
    placed_path=ROOT/'analysis/native-s00-placed-units.json'
    if placed_path.exists():
        placed=json.loads(placed_path.read_text(encoding='utf-8'))
        if not placed.get('placement_checks_passed'):
            raise ValueError('Run native placement checks before migration')
        by_id={u['unitId']:u for u in placed['units']}
        for unit in data['units']:
            unit['nativePlacement']=by_id[unit['unitId16']]
        data['placement_scope']=placed['scope']
        data['placed_count']=placed['placed_count']
    text=json.dumps(data,ensure_ascii=False,indent=2)
    path.write_text(text,encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/data/scenarios/S_00-units-native.json').write_text(text,encoding='utf-8')
    print(f'Attached {len(lookup)} native expansions; {len(changed)} art differences from first-side links')


if __name__=='__main__':main()
