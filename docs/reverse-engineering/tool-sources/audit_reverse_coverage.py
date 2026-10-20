"""Build a conservative coverage/gap report from authoritative verification artifacts."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'analysis/verification-manifest.json').read_text(encoding='utf-8'))
checks=[{'name':row['name'],'metric':row['metric'],'passed':bool(row.get('passed'))}
        for row in manifest['checks']]
gaps=[
 {'area':'target selection','evidence':'tools/verify_native_target_candidates.py','status':'probe-failed','reason':'native target-list/view initialization exits before a trusted result'},
 {'area':'combat result writeback','evidence':'analysis/native-main/pseudocode/004404bd.c','status':'static-only','reason':'damage/status result rendering and persistence are not dynamically exercised end-to-end'},
 {'area':'win/loss and turn termination','evidence':'analysis/battle-turn-static-chain.md','status':'partial','reason':'turn transition callers are indexed, but all victory-condition branches are not dynamically verified'},
 {'area':'resource DLL function graphs','evidence':'analysis/dll-and-runtime-coverage.md','status':'partial','reason':'resource maps and exports are verified; every DLL internal call graph is not reconstructed'},
 {'area':'Data.e5 sparse entries 6-9','evidence':'analysis/data-sparse-entry-summary.md','status':'open','reason':'decoded and structurally summarized, but no runtime loader semantics found'},
 {'area':'E partition tail semantics','evidence':'analysis/e-partition-tail-sparsity.md','status':'partial','reason':'battle prefix and serialization are recovered; 5399-byte sparse tail semantics remain unresolved'},
 {'area':'real window combat input','evidence':'analysis/player-movement-and-cancel.md','status':'partial','reason':'movement was tested through controlled native input callbacks, not full Windows UI event flow'},
]
result={'generated':'2026-10-17','passedChecks':len([c for c in checks if c['passed']]),
        'totalChecks':len(checks),'checks':checks,'knownGaps':gaps,
        'completionClaim':False}
(ROOT/'analysis/reverse-coverage-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'analysis/reverse-coverage-audit.md').write_text('''# 逆向覆盖审计\n\n本报告由 `tools/audit_reverse_coverage.py` 生成。验证清单中的检查项只表示对应范围有证据，不表示整个游戏已经完成逆向。\n\n## 当前证据\n\n`analysis/verification-manifest.json` 中的检查项全部标记通过，共 {passed}/{total} 项。\n\n## 明确缺口\n\n- 目标筛选探针尚未产生可信动态结果。\n- 战斗结果写回、死亡/反击以及胜负和回合终止仍未完成端到端动态验证。\n- 资源 DLL 的资源映射和导出表已审计，但内部函数调用图未全部恢复。\n- `Data.e5` 稀疏条目 6-9 仍开放。\n- 移动使用受控 native 输入验证，真实窗口战斗输入和菜单事件流仍缺证据。\n\n因此机器报告明确保留 `completionClaim: false`，不会用已通过的局部检查替代原始“完整逆向”目标。\n'''.format(passed=result['passedChecks'],total=result['totalChecks']),encoding='utf-8')
audit_note = (ROOT/'analysis/reverse-coverage-audit.md').read_text(encoding='utf-8')
audit_note += '\n\n## Current gap count\n\nThe machine-readable report contains exactly %d known gaps. The E-partition fixed layout and battle prefix are covered; only the 5399-byte tail semantics remain open for that format.\n' % len(gaps)
(ROOT/'analysis/reverse-coverage-audit.md').write_text(audit_note,encoding='utf-8')
print(f"Coverage audit: {result['passedChecks']}/{result['totalChecks']} checks; {len(gaps)} known gaps")
