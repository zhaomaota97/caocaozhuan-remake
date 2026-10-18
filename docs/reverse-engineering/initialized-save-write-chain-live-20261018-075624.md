# Initialized save write chain live evidence

The observer was changed so direct commands wait for a nonzero
`DAT_00496F60`, and command dispatch retries after the battle window list is
available. In run `analysis/live-startup-20261018-075624/events.jsonl`:

- normal initialization completed;
- `WM_COMMAND 101` was accepted (`queued=true`);
- `FUN_0041B16A` entered with a nonzero save buffer `0xA0B978`;
- after confirmation, the native process began creating the D/S save-partition
  files and continued running without the previous null write at `0x41B233`.

This is the first live trace that reaches the real initialized save serializer
and its file-creation side effects.

The remaining boundary is slot conversion: the serializer receives
`0xFFFFFFFF` for the automatically selected slot-0 path, and the file-open
trace shows malformed encoded names (`SV...D/S.E5S`) rather than a clean
`SV00D/S.E5S` pair. Therefore this run proves entry into the write chain, but
not a valid completed slot-0 file replacement. The slot-list activation helper
needs a native coordinate/selection correction before claiming a full UI
roundtrip.
