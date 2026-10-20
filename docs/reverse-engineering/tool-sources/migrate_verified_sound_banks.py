"""Copy every native-verified sound ID to an independent, hashed remake bank."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMAKE = ROOT.parent/'caocaozhuan-remake'
validation = json.loads((ROOT/'analysis/native-sound-mapping-validation.json').read_text(encoding='utf-8'))
planned = []
for row in validation:
    if 'expected' not in row:
        continue
    if not row.get('match') or not row.get('file_exists'):
        raise RuntimeError(f"Unverified sound ID {row.get('id')}")
    source = ROOT/'analysis/runtime-game'/row['expected']
    payload = source.read_bytes()
    planned.append((row['id'], source, hashlib.sha256(payload).hexdigest(), len(payload)))
if len({row[0] for row in planned}) != len(planned):
    raise RuntimeError('Duplicate sound IDs')
assets = REMAKE/'public/assets/audio/native'
assets.mkdir(parents=True, exist_ok=True)
records = []
for sound_id, source, digest, size in planned:
    destination = assets/source.name.lower()
    shutil.copy2(source, destination)
    if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
        raise RuntimeError(f'Copy verification failed: {destination}')
    records.append({'id':sound_id,'originalName':source.name,
                    'url':'/assets/audio/native/'+destination.name,
                    'sha256':digest,'bytes':size})
manifest = {'selector':'0x474777','sourceEvidence':'native-sound-mapping-validation.json',
            'count':len(records),'sounds':records}
(REMAKE/'data/mappings/native-sound-assets.json').write_text(
    json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
probes = json.loads((ROOT/'analysis/native-movement-sounds.json').read_text(encoding='utf-8'))
if probes['matched'] != probes['total']:
    raise RuntimeError('Movement sound selector has unmatched probes')
by_id = {row['id']:row for row in records}
rules = []
for row in probes['rows']:
    if not row['match']:
        raise RuntimeError('Invalid movement sound probe')
    sounds = [by_id[call['id']] for call in row['calls']]
    rules.append({'movementType':row['movementType'],'terrain':row['terrain'],
                  'soundIds':[sound['id'] for sound in sounds],
                  'urls':[sound['url'] for sound in sounds]})
(REMAKE/'data/mappings/movement-sounds.json').write_text(json.dumps({
    'selector':'0x43F38B','evidence':'native-movement-sounds.json','rows':rules},indent=2)+'\n',encoding='utf-8')
print(f'Copied and SHA-256 verified {len(records)} native sounds; mapped {len(rules)} movement cases')
