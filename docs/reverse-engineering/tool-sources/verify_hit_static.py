"""Verify the statically recovered ordinary-hit probability path."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "analysis/native-main/pseudocode/0043b50d.c").read_text(encoding="utf-8")
checks = {
    "reads_attacker_defender_stat": "FUN_0043f631(piVar2)" in src and "FUN_0043f631(this_00)" in src,
    "uses_rng": "FUN_0047fa9e" in src,
    "has_zero_result_branch": "local_14 = 0" in src,
    "has_full_result_branch": "local_14 = 100" in src,
    "checks_defender_flag_08": "FUN_004066e0(this_00,8)" in src,
}
for name, passed in checks.items():
    print(f"{name}: {'PASS' if passed else 'FAIL'}")
if not all(checks.values()):
    raise SystemExit(1)
print("Ordinary hit static chain: 5/5")
