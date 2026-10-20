"""Derive a readable projection of the native combat writeback boundary.

This is intentionally evidence-only: it records offsets and formulas visible in
the recovered pseudocode, without inventing HP/MP names where the native code
only exposes bounded fields.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
out = {
    "routine": "FUN_00405889",
    "input_record": {"base": "param_1", "terminator": {"offset": "0x10+index", "value": "0xff"}},
    "per_actor_inputs": [
        {"name": "primary_result", "offset": "0x84 + index*4", "type": "i32"},
        {"name": "secondary_result", "offset": "0x254 + index*4", "type": "i32"},
        {"name": "effect_amount", "offset": "0x430 + index*4", "type": "u32"},
    ],
    "live_actor": {"base": "0x004B2C50", "stride": "0x24", "record_size": 36,
                    "index": "param_1[1]"},
    "flag_updates": [
        {"predicate": "item/category '#' or status gate '2'", "mask": "0x08"},
        {"predicate": "item/category '$' or status gate '1'", "mask": "0x10"},
        {"predicate": "item/category '%' or status gate '*'", "mask": "0x02"},
        {"predicate": "item/category '&'", "mask": "0x04"},
    ],
    "bounded_writebacks": [
        {"helper": "FUN_0043F6CD", "source": "FUN_00472C90(live_actor) - primary_result", "field_semantics": "bounded live resource field A"},
        {"helper": "FUN_0043F70E", "source": "FUN_00472840(live_actor) - secondary_result", "field_semantics": "bounded live resource field B"},
    ],
    "presentation": {
        "animation_or_effect": "FUN_00450984(unit, side, primary_result, secondary_result, 0, 0, effect_amount, bVar1==0)",
        "equipment_or_inventory": "FUN_004082D6(0x004A1B68 + equipment_index*0x48, 1, effect_amount)",
        "clear_after_action": {"helper": "FUN_00406690", "mask": "0x20"},
    },
    "serialization_note": "The 26-byte compact actor record is serialized later; this routine writes the 36-byte live actor object and must not be offset-mapped byte-for-byte.",
    "evidence": ["analysis/native-main/pseudocode/00405889.c", "analysis/combat-writeback-layout-distinction-20261018.md", "analysis/combat-writeback-field-offsets-static-20261018.md"],
}
(ROOT / "analysis/native-combat-writeback-projection.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
lines = ["# Native combat writeback projection", "", "Generated from `FUN_00405889` pseudocode; field names remain neutral where only offsets are proven.", ""]
lines += ["- Live actor table: `0x004B2C50`, stride `0x24` (36 bytes).", "- Input arrays: primary `+0x84`, secondary `+0x254`, effect `+0x430`, each indexed by the action record index.", "- Bounded writes: `0x43F6CD` receives current field A minus primary result; `0x43F70E` receives current field B minus secondary result.", "- Flags: masks `0x08`, `0x10`, `0x02`, `0x04` are set by the four native predicates.", "- Cleanup: `0x406690(..., 0x20)` clears the post-action flag.", "", "The compact 26-byte save actor record is a later serialization projection, not the same memory layout."]
(ROOT / "analysis/native-combat-writeback-projection.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("wrote native-combat-writeback-projection.json and .md")
