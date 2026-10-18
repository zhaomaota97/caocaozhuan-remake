# Save buffer initialization boundary

Static analysis shows `FUN_0041BF67` is the startup initializer that assigns
`DAT_00496F60 = FUN_0047FA40(&DAT_004AAB68, 0, 0, 4)` and then loads DATA.E5
entry 0 into that buffer through `FUN_0041B666`.

The observer now hooks `FUN_0041BF67`, `FUN_0047FA40`, and `FUN_0041B16A`.
In run `analysis/live-startup-20261018-074210/events.jsonl`:

- no `save-state-init-enter` event occurred;
- no `save-buffer-alloc-enter` event occurred;
- `save-serializer-enter` did occur with slot `0xFFFFFFFF` and buffer `0x0`;
- the process faulted at `Ekd5.exe+0x41B233` writing through that null buffer.

This proves the observed startup/new-game path reaches the save dialog without
executing the normal `FUN_0041BF67` initialization routine. The null buffer is
therefore an incomplete runtime setup path in the observer scenario, not
evidence that the native initializer itself allocates null. The static
initializer chain and the dynamic omission are now both recorded for the next
probe, which should enter through the normal main initialization instead of
the forced skip/automated path.
