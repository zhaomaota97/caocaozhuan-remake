# Live battle surface observation

The observer now recognizes a battle surface from the native control pair
`HexMapName` plus `ToolbarWindow32`, even when the internal battle-ready RVA is
not reached. A new-game run captured:

- main window `640x489` at the native battle layout;
- toolbar control id `113`, class `ToolbarWindow32`;
- toolbar button count `10`;
- native resource loading including `HITAREA.E5`.

Raw evidence: `analysis/live-startup-20261018-044715/events.jsonl`.

The run terminated after a legacy common-controls access violation while the
experimental toolbar click probe was active. It proves battle-surface
detection and toolbar enumeration, but does not claim button-command or
select/cancel sound identity.

The same surface detector is now shared by `--move-test`; a controlled run
reached the same native common-controls failure before the input loop, so no
`0x438308` UI event is promoted from that run. Direct movement probes remain
separate and continue to validate the native path geometry.
