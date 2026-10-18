# Direct save command live rerun

Run:

```text
python tools/observe_live_game.py --start-new --advance-story --skip-intro --direct-commands 101 --seconds 25
```

Raw evidence:
`analysis/live-startup-20261018-073405/events.jsonl`.

The battle root accepted command `101` (`queued=true`). The original process
then opened a modal window titled `保存进度` and kept it open for the remaining
bounded run. Its controls were:

- button id `2`: `取消`
- static id `65535`: `请选择保存哪个进度。`
- `SysListView32` id `1487`: save-slot list
- `SysHeader32`: list header

The trace also reads both per-slot save partitions for slots 00 through 09:
`SV00D.E5S` ... `SV09D.E5S` and `SV00S.E5S` ... `SV09S.E5S`, with observed
payload sizes of 49 and 50 bytes respectively. This confirms the runtime save
dialog's slot enumeration and file naming/partition relationship.

The run did not activate a slot or confirm the write, so it proves the save
dialog and read-side slot discovery, not a completed UI save round trip.
