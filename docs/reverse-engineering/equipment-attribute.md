# Equipment attribute contribution

The original item loader `0x40C537` and contribution function `0x40C674`
were executed for all 104 original DATA item definitions at stored levels
0, 1, 2, 3, 8, 9, 10, 49, 99 and 255. All 1,040 results matched.
No game UI or audio was started.

Runtime item offsets: category `+0x11`, base contribution `+0x15`,
per-level increase `+0x17`. Original input fields at these three offsets
are copied directly by the loader. The exported `growthValue` is distinct
from the secondary-effect value at runtime offset `+0x16`.

For categories below 18, contribution is
`min(255, base + max(0, storedLevel - 1) * growthValue)`.
Other categories return the base unchanged. Level 0 is explicitly covered
and produces the same contribution as level 1. The item contribution helper
does not apply the equipment XP cap (3 or 9) before calculating the value.

Raw definitions and native returns: `native-equipment-attribute.json`.
Readable Web implementation: `src/rules/equipmentAttribute.ts`.

Reproduce from the reverse workspace:

```powershell
python tools/verify_equipment_attribute.py
```

This validates a single-item contribution. It does not yet validate the
complete `0x407C0E` slot accumulator, secondary effect selection, or the
actor state modifiers. No duplicate correction is applied to the current
Web combat snapshots, which already contain the native equipment effect.
