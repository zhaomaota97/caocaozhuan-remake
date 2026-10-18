# Save slot raw path failure

The `CreateFileA` hook now records raw path bytes and return handles. In run
`analysis/live-startup-20261018-075933/events.jsonl`:

- normal existing slot reads such as `SV01D.E5S` and `SV01S.E5S` contain plain
  ASCII bytes and return valid handles;
- after confirming the automated slot-0 save, the native path bytes contain
  `SV C9 35 D.E5S` (and corresponding E/S variants), not `SV00D.E5S`;
- every attempted open of that malformed path returns `0xFFFFFFFF`.

Therefore the remaining UI-save gap is precisely the slot-selection conversion
before `FUN_0041B16A`: the serializer buffer and write chain are valid, but the
automated list activation leaves an invalid internal slot value that formats as
bytes `C9 35`. This is now demonstrated from raw bytes and Win32 handles,
independent of text encoding.
