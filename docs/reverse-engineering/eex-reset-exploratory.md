# EEX opcode 68 reset validation

Static handler `0x412230` does three things: clears 256 interpreter-table
entries through `0x4184D1`, calls `0x426C32`, then iterates 115 records in
global scenario object `0x492F90`, setting each record's first dword to
`0xFFFF` and its third dword to zero. It then copies the non-`0xFFFF`
initial record IDs from table `0x48B350` back into the first dword of the
corresponding records and returns 1.

`tools/verify_eex_reset_native.py` executes the native handler and passes
the full controlled boundary. The interpreter object is allocated at a
controlled address with its 256-entry table at `object+0x38`; all 256 entries
are zeroed. The global record table is then observed for all 115 entries:
each record's flags are zero and the first field is copied from the native
initial-ID table until its first `0xFFFF` terminator. The result and raw
output are in `native-eex-reset-validation.json`.

The static record reset and the independent opcode-10 table-clear verifier
are separate facts. This probe establishes the opcode-68 object layout and
the complete reset/copy boundary, but does not establish when the story
dispatcher chooses to execute opcode 68 in a full script.
