"""One-time export; this tool stays in the reverse workspace, never in the game runtime."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root.parent / 'caocaozhuan-remake/data/saves/slot-08.json'
save = json.loads(target.read_text(encoding='utf-8-sig'))
raw = (root / 'Sv08s.e5s').read_bytes()
for unit in save['actors']:
    slot = int(unit['id'].split('-')[1])
    record = raw[1301 + slot * 26:1301 + (slot + 1) * 26]
    unit['hp'] = int.from_bytes(record[2:4], 'little')
    unit['direction'] = record[17]
    unit['actorFlags'] = record[15]
    unit['statusFlags'] = record[24]
    unit['mirror'] = bool(record[15] & 8)
    # Injured pose requires maximum health from expanded roster; do not guess it.
    unit['injuredPose'] = None
save['animationPhase'] = raw[35 + 11]
save['animationStepMs'] = 400
save['animationEvidence'] = ['0x43E572', '0x43E515', '0x406730', '0x4541A9', '0x42C4CB', '0x47EB97', '0x442E26']
target.write_text(json.dumps(save, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f"Exported {len(save['actors'])} actor direction/status records; phase={save['animationPhase']}")
