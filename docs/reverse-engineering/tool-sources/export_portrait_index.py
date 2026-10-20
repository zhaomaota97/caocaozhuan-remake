"""Inventory FACE entries and transcribe the static selector at 0x4075A7."""
import hashlib
import json
from pathlib import Path

from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]


def portrait_index(character_id, stored_index, flags, phase):
    character_id &= 0xFFF
    if character_id == 0:
        variant = flags & 15
        return (4 if phase >= 2 else 0) + (variant if variant in (1, 2, 3) else 0)
    if character_id == 1:
        if flags & 15 == 4:
            return 224
        return stored_index + 7 if flags & 128 else 223
    special = {35: (16, 214), 8: (32, 226), 4: (64, 227)}
    if character_id in special:
        bit, index = special[character_id]
        if flags & bit:
            return index
    return stored_index + 7


def main():
    resources = []
    for index, raw in entries(ROOT / 'Face.e5'):
        resources.append(dict(index=index, size=len(raw),
                              matches_64x80=len(raw) == 64 * 80,
                              sha256=hashlib.sha256(raw).hexdigest()))
    cases = []
    for actor in (0, 1, 35, 8, 4, 2):
        for phase in (0, 2):
            for flags in (0, 1, 2, 3, 4, 16, 32, 64, 128):
                cases.append(dict(character_id=actor, stored_index=actor,
                                  flags=flags, phase=phase,
                                  resource=portrait_index(actor, actor, flags, phase)))
    result = dict(evidence='static transcription, not native differential validation',
                  selector='0x4075A7', character_id='word(unit+0) & 0xFFF',
                  stored_index='int32(unit+4)', flags='byte(0x4B0770+0x11)',
                  phase='byte(0x4B0770+6)', width=64, height=80,
                  dimension_evidence='0x432ED9 and 0x46D749 blit arguments',
                  resources=resources, selector_examples=cases)
    target = ROOT / 'analysis/portrait-index.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(resources)} FACE entries; '
          f'{sum(r["matches_64x80"] for r in resources)} match 64x80; '
          f'{len(cases)} static selector examples. {target}')


if __name__ == '__main__':
    main()
