# Normal save-buffer allocation live evidence

After correcting the allocator RVA (`FUN_0047FA40` -> RVA `0x7FA40`), the
normal startup trace captured the real initialization allocation:

- `FUN_0041BF67` entered.
- `FUN_0047FA40(..., size=4796304)` returned `0xA60FE8`.
- The allocation is followed by the native DATA.E5 initialization sequence.

The same trace also records earlier allocator calls for unrelated startup
objects (`4909904`, `1336`, `16777216`) and small table entries, so the large
`4796304` call is identified by its ordering immediately after
`save-state-init-enter`, not by size alone.

Raw evidence:
`analysis/live-startup-20261018-074651/events.jsonl`.

This closes the positive allocation side of the save initialization chain. The
initializer remains modal and did not return during the bounded run, so the
assignment of the returned pointer into `DAT_00496F60` is still tracked as a
pending return-side observation.
