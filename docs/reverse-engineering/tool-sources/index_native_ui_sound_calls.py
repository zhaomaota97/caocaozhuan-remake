"""Index static callers of the native SE_E/SE sound wrapper."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rows=[]
for path in sorted((ROOT/'analysis/native-main/pseudocode').glob('*.c')):
    text=path.read_text(encoding='utf-8',errors='replace')
    for match in re.finditer(r'FUN_0047467a\([^,]+,([^,\)]+),([^\)]+)\)',text):
        value=match.group(1).strip(); mode=match.group(2).strip()
        rows.append({'caller':path.stem,'line':text[:match.start()].count('\n')+1,
                     'soundExpression':value,'modeExpression':mode,
                     'constantId':int(value,0) if re.fullmatch(r'(?:0x[0-9a-fA-F]+|\d+)',value) else None})
result={'wrapper':'0x47467A','wrapperSemantics':'SE_E/SE sound filename selector and sndPlaySoundA dispatch','calls':rows,
        'constantIds':sorted({row['constantId'] for row in rows if row['constantId'] is not None})}
(ROOT/'analysis/native-ui-sound-calls.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('indexed',len(rows),'calls;',len(result['constantIds']),'constant IDs')
