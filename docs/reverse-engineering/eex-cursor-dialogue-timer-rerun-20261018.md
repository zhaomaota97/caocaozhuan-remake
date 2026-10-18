# EEX cursor/dialogue/timer native rerun

Additional native probes passed:

- cursor slot-5/tag readers: all 9 scalar/string/mismatch cases;
- opcode 9 wait timer: `5/5`;
- opcode 20 dialogue parsing: `11/11`.

The cursor probe covers CP936 strings, DWORD/WORD scalar reads, mismatch
sentinels, and raw opcode tags. These results expand verified EEX parser and
handler semantics without relying on GUI story progression.
