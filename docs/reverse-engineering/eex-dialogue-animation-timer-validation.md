# EEX Dialogue, Animation, and Timer Validation

Additional native handler probes pass:

- Opcode 20 dialogue parsing: 11/11 cases.
- EEX animation command decoding/execution boundaries: 970/970 cases.
- Opcode 9 wait-timer semantics: 5/5 cases.

These validate the script cursor, dialogue parameter forms, animation command boundaries, and the 50 ms timer status path independently of a full story playthrough.
