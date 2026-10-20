"""Verify the statically recovered Yuxi critical-hit chain."""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
items = ROOT / "analysis" / "items.csv"
src_item = (ROOT / "analysis/native-main/pseudocode/0041c4e9.c").read_text(encoding="utf-8")
src_attack = (ROOT / "analysis/native-main/pseudocode/004404bd.c").read_text(encoding="utf-8")
rows = list(csv.DictReader(items.open(encoding="utf-8-sig")))
yuxi = next(row for row in rows if row["name"] == "玉玺")
checks = {
    "yuxi_id_82": yuxi["id"] == "82",
    "yuxi_category_41": yuxi["category_byte"] == "41",
    "category_41_checks_flag_08": "case 0x41:" in src_item and "FUN_004066e0(this,8)" in src_item,
    "attack_calls_item_predicate": "FUN_0041c4e9" in src_attack,
    "critical_probability_100": "& 100" in src_attack and "iVar6 != 0" in src_attack,
}
for name, passed in checks.items():
    print(f"{name}: {'PASS' if passed else 'FAIL'}")
if not all(checks.values()):
    raise SystemExit(1)
print("Yuxi critical static chain: 5/5")
