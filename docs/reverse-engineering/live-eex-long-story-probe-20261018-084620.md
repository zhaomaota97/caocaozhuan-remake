# Long live EEX story probe

Run:

```text
python tools/observe_live_game.py --start-new --advance-story --skip-intro --seconds 60
```

Raw stream:
`analysis/live-startup-20261018-084620/events.jsonl`.

The bounded run captured EEX handler opcodes:

`2, 8, 10, 28, 35, 39, 47, 48, 50, 58, 59, 62`

It also requested 14 distinct runtime resources, including `DATA.E5`,
`FACE.E5`, `HITAREA.E5`, `IMSG.E5`, `MMAP.E5`, `PMAP.E5`, `PMAPOBJ.E5`,
`PMPALET.E5`, `UNIT_MOV.E5`, and `R_00.EEX`.

This is additional independent runtime evidence, not full story coverage: the
run still follows the startup/first-battle path and does not reach every EEX
script or victory/loss branch.
