# EEX Handler Batch Validation

The current native handler batch passes the following additional cases:

- Amount updates: 96/96
- Common configuration: 252/252
- Effect dispatch/resource selection: 2,560/2,560, with missing-key commit count 0
- Numeric predicates: 360/360
- Opcode 48 target ABI boundary: passed
- Opcode 50 missing/non-type-4 boundaries: passed
- Opcode reset table: 256 records reset to `0xffff`/zero flags
- Unit restoration: 288/288
- Unit counting: 6,144/6,144
- Config predicates (opcodes 66/67): passed all eight cases

These are isolated native handler validations; they increase opcode and state coverage but do not replace a complete story or AI turn trace.
