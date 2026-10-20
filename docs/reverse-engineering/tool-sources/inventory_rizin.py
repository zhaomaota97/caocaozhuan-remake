"""Collect bounded Rizin function inventories for shipped DLLs."""
import json
import subprocess
from pathlib import Path

rows=[]
for path in sorted(Path('.').glob('*.dll')):
    cmd=[r'C:\Program Files\Rizin\bin\rizin.exe','-q','-c','aaa','-c','aflj',str(path)]
    result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
    try: functions=json.loads(result.stdout or '[]')
    except json.JSONDecodeError: functions=[]
    rows.append({'file':path.name,'function_count':len(functions),
                 'functions':[{'address':f.get('offset'),'name':f.get('name'),'size':f.get('size')} for f in functions],
                 'stderr_tail':result.stderr[-500:]})
Path('analysis/dll-rizin-inventory.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
for r in rows: print(r['file'],r['function_count'])
