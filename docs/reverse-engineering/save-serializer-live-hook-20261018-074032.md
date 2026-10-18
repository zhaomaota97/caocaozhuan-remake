# Save serializer live hook

The observer now hooks `FUN_0041B16A` using the correct x86 `__thiscall`
convention (`ECX` is the `this` pointer and the first native argument is the
slot selector). In the latest confirmation run:

- serializer `this`: `0x6CEEA0`
- slot argument: `0xFFFFFFFF` (the native zero-based slot-0 path)
- global save buffer pointer at `DAT_00496F60`: `0x0`
- subsequent fault: `Ekd5.exe+0x41B233`, write to address `0x0`

Raw evidence:
`analysis/live-startup-20261018-074032/events.jsonl`.

This proves the failure is a null global save-buffer initialization at the
serializer boundary, rather than an invalid slot index or file path. The hook
also validates the recovered `FUN_0041B16A` calling convention and gives a
precise target for future initialization/state setup probes.
