"""Export the recoverable, pure target-type predicates used by 0x420422."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def accepted(kind, terrain):
    if kind == 0:
        return terrain in {0, 1, 2, 8, 16, 18, 19, 20, 21, 22, 23, 24}
    if 5 <= kind <= 9:
        return 7 <= terrain <= 10 or terrain == 13
    if 10 <= kind <= 14:
        return terrain in {0, 1, 3, 4, 7, 8, 9, 10, 13}
    if 15 <= kind <= 19:
        return 3 <= terrain <= 4
    return None


def main():
    rows = []
    for start, end in ((0, 4), (5, 9), (10, 14), (15, 19)):
        rows.append(dict(kinds=list(range(start, end + 1)),
                         accepted_terrain=[i for i in range(256) if accepted(start, i)],
                         source={'function': '0x420422', 'predicate':
                                 {0: '0x420AB6', 5: '0x420B17', 10: '0x420B42',
                                  15: '0x420B98'}[start]}))
    result = dict(function='0x420422', effect_type_field='0x4AF4C0[type]+0x0B',
                  groups=rows,
                  exact_pure_predicates=True,
                  caveat='outer function also checks effect-side target restrictions, status flags, class and faction; this file exports only four pure terrain-kind predicates')
    target = ROOT / 'analysis/effect-target-predicates.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Exported {len(rows)} pure effect target groups to {target}')


if __name__ == '__main__':
    main()
