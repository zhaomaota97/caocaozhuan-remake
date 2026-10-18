# Unit, equipment and growth rerun

The unit data export and native checks were rerun:

- Character table: `analysis/characters.csv`
- Class growth records exported: `53`
- Item records exported: `104`
- Slot-08 attack ranges: `32/32`
- Growth native fixtures: `3/3`
- Unit XP/level/growth: `22896/22896`
- Equipment XP/levels/notifications: `18900/18900`

There is no `verify_equipment_category.py` in the current tool set; the
category predicates are covered by the existing attack-range and equipment XP
verifiers, so no nonexistent test is counted as a pass.
