# Live save/load battle probe (2026-10-18 07:21:05)

## Invocation

`tools/observe_live_game.py --open-load --load-slot 8 --confirm-load --probe-toolbar --save-command --save-test --move-test --seconds 45`

## Evidence

The load path reached the battle surface before the legacy control boundary
failed. The captured event stream is
`analysis/live-startup-20261018-072105/events.jsonl`.

The native control tree included `ToolbarWindow32` (id `113`, 10 buttons),
`HexMapName`, three `HexTurnName` controls, `Weather`, `SoldierFace`,
`SoldierChar`, `Effect`, `Influence`, `MgcEffect`, `MgcInfluence`,
`ButaiSlct`, `GoButaiSlct`, `Practice`, `PracMesBox`, `TokugiEff`, and
`TokugiInf`.

The observer recorded the following boundary exception:

`COMCTL32.dll` access violation during the toolbar/control path, with the
native call chain reaching `Ekd5.exe+0x462a06`, `Ekd5.exe+0x46380b`, and
`Ekd5.exe+0x462963`.

The process then terminated without a game crash classification. This explains
why toolbar probing and UI save/load roundtrip cannot yet be claimed as
verified. The raw stream remains available for later hook refinement.

## EEX observation

The run again observed handler opcodes `9,20,28,35,48,50,51`; these are
additional runtime evidence, not a claim of complete EEX story coverage.
