"""Verify that reverse-validated runtime assets exist in the standalone remake."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REMAKE=ROOT.parent/'caocaozhuan-remake'/'public'/'assets'
sound=json.loads((REMAKE.parent.parent/'data'/'mappings'/'native-sound-mapping-validation.json').read_text(encoding='utf-8'))
rows=[]
for item in sound:
    expected=item.get('expected');
    if not isinstance(item.get('id'),int) or not expected: continue
    path=REMAKE/'audio'/'native'/expected.lower()
    rows.append({'id':item['id'],'expected':expected,'path':str(path.relative_to(REMAKE.parent.parent)),'exists':path.is_file()})
effects=list((REMAKE/'effects').glob('Mcall*.gif'))
maps=list((REMAKE/'maps').glob('battle-*.png'))
animations=list((REMAKE/'animations'/'movement-map31').glob('mov-*.png'))
result={'validatedSoundRows':len(sound),'uniqueSoundFiles':len(rows),'soundPresent':sum(x['exists'] for x in rows),'effectGifs':len(effects),'battleMaps':len(maps),'movementSheets':len(animations),'missingSounds':[x for x in rows if not x['exists']]}
(REMAKE.parent.parent/'data'/'mappings'/'remake-asset-migration-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
if result['missingSounds']: raise SystemExit(1)
