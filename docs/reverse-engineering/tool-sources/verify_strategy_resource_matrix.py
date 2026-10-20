"""Expand native strategy resource writeback coverage using the existing harness."""
import ast
import itertools
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]
tree=ast.parse((ROOT/'tools/verify_effect_cost_native.py').read_text(encoding='utf-8'))
source=next(n.args[0].value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='create_script')
start=source.index('  for (const t of [')
end=source.index('  ]) {',start)+len('  ]) {')
source=source[:start]+'  for (const t of cases) {'+source[end:]
source=source.replace('verify() {','verify(cases) {').replace('action.add(0x4ac).writeU32(1);','action.add(0x4ac).writeU32(t.success?1:0);')
cases=[dict(success=success,effect=effect,current=mp,cost=cost,divisor=divisor,magnitude=magnitude)
       for success,effect,mp,cost,divisor,magnitude in itertools.product([False,True],[0,20,22],[0,1,13,40,50,90],[0,1,13,255],[None,2,3,20],[0,7,30])]
device=frida.get_local_device()
pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'))
session=None
try:
    session=device.attach(pid);script=session.create_script(source);script.load()
    rows=script.exports_sync.verify(cases)
    for row in rows:
        hp=80;mp=row['current']
        if row['success']:
            mp=max(0,mp-row['cost']//(row['divisor'] or 1))
            if row['effect']==20:hp+=min(row['magnitude'],100-hp)
            elif row['effect']==22:mp+=min(row['magnitude'],50-mp)
            hp=min(100,hp);mp=min(50,mp)
        row['expected']=dict(hp=hp,mp=mp)
        row['match']=row['health']==hp and row['resource']==mp
    report=dict(total=len(rows),passed=sum(row['match'] for row in rows),rows=rows,scope='native 0x422F0D with presentation/rewards/refresh callbacks suppressed; controlled max HP100 MP50; no eligibility or full effect execution')
    text=json.dumps(report,indent=2)+'\n'
    (ROOT/'analysis/native-strategy-resource-matrix.json').write_text(text,encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-strategy-resource-matrix.json').write_text(text,encoding='utf-8')
    print(f'Native strategy resource matrix: {report["passed"]}/{report["total"]}')
    if report['passed']!=report['total']:raise RuntimeError(next(row for row in rows if not row['match']))
finally:
    device.kill(pid)
    if session:session.detach()
