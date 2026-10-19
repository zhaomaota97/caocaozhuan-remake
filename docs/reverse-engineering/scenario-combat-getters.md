# Scenario combat getter snapshots

Native export now captures attack (`0x43F4FE`), defense (`0x43F595`),
agility (`0x43F631`) and luck (`0x43F67F`) for every initialized actor in
all 58 controlled scenario expansions. These are calls to native getter
functions, not guessed calculations from record bytes.

Reproduce in the reverse workspace:

```powershell
python tools/export_all_level_units_native.py
```

The exporter uses `capture_s00_expanded_units_native.py`, the original DATA
loaders, native scenario presets and placement functions. Each scenario is
isolated in a suspended native process. Existing UI and presentation stubs
remain in place. All 58 placement checks passed after adding getter capture.

The raw results are bundled in `data/scenarios/native-units/S_00..S_57.json`.
Within the remake, run `node tools/build-scenario-combat.mjs` to produce
`data/mappings/scenario-combat-runtime.json`. Battle actor construction reads
these snapshots by scenario and native slot. Slot-08 actors retain their
separate saved-state snapshots.

Scope: controlled default-party initialization, not a campaign playthrough.
Equipment changes, temporary status modifiers and later script changes need
native attribute recalculation rather than indefinitely reusing snapshots.
The browser S_01 test compares all living actors' four attributes directly
with raw native capture output.
