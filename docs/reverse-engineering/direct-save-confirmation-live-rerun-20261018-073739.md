# Direct save confirmation live rerun

Run:

```text
python tools/observe_live_game.py --start-new --advance-story --direct-commands 101 --save-slot 0 --confirm-save --seconds 35
```

Raw evidence:
`analysis/live-startup-20261018-073739/events.jsonl`.

The run reached the native save dialog, activated slot 0, and produced the
original confirmation window titled `保存`. The observer clicked its `是`
button (control id `6`) and recorded the native entry immediately afterward.
The process then terminated at an access violation in `Ekd5.exe+0x41B233`,
with callers `+0x41ACC0`, `+0x46535B`, `+0x465180`, and `+0x462963`.

Static pseudocode identifies the containing routine `FUN_0041B16A` as the save
serializer: it constructs slot-specific `SV%02dD/S` paths, serializes the
global state, 128 effect records, and 512 actor records, then writes the two
partitions. `FUN_0041AC86` dispatches dialog completion to `FUN_0041B16A` when
the save dialog mode is active.

This closes the UI path through slot selection and confirmation and identifies
the exact native write routine. The null write at `0x41B233` is retained as a
runtime boundary; it does not invalidate the static save-layout and command
chain evidence.
