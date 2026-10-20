"""Build one machine-readable EEX static/live/native coverage summary."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
matrix=json.loads((ROOT/'analysis/eex-coverage-matrix.json').read_text(encoding='utf-8'))
live=json.loads((ROOT/'analysis/live-eex-opcode-union.json').read_text(encoding='utf-8'))
priority=json.loads((ROOT/'analysis/unobserved-eex-priority.json').read_text(encoding='utf-8'))
native={}
for name in ['native-eex-low-frequency-validation.json','native-eex-conditional-validation.json',
             'native-eex-enemy-setup-validation.json','native-eex-restore-units-validation.json',
             'native-eex-amount-validation.json','native-eex-animation-command-validation.json',
             'native-eex-high-frequency-validation.json','native-eex-effect-dispatch-validation.json']:
    path=ROOT/'analysis'/name
    if path.exists():
        try:native[name]=json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:native[name]={'parseError':True}
summary={'static':{'total':matrix.get('total'),'dynamic':matrix.get('dynamic'),'staticOnly':matrix.get('static'),'reserved':matrix.get('reserved')},
         'live':{'runs':live['runCount'],'unionCount':live['unionCount'],'opcodes':live['union']},
         'nativeProbeArtifacts':sorted(native),
         'unobservedPriorityCount':len(priority['candidates']),
         'completionClaim':False}
(ROOT/'analysis/eex-coverage-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary['static']|{'liveUnion':summary['live']['unionCount'],'priority':summary['unobservedPriorityCount']},ensure_ascii=False))
