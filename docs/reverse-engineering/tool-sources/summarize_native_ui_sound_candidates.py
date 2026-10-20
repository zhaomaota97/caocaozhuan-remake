"""Group native sound-wrapper callers by constant ID for focused UI tracing."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'analysis/native-ui-sound-calls.json').read_text(encoding='utf-8'))
groups={}
for row in data['calls']:
    key=str(row['constantId']) if row['constantId'] is not None else 'dynamic'
    groups.setdefault(key,[]).append({'caller':row['caller'],'line':row['line'],'mode':row['modeExpression']})
out={'wrapper':data['wrapper'],'constantGroups':groups,
     'note':'Static candidates only; UI event labels require dynamic call-stack correlation.'}
(ROOT/'analysis/native-ui-sound-candidates.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('grouped',len(groups),'sound candidates')
