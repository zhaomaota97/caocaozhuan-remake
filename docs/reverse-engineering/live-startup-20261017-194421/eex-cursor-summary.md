# Live EEX cursor evidence

Source: `analysis\live-startup-20261017-194421\events.jsonl`

Interpreter snapshots: 1; dispatches: 26; handler observations: 17.

- Interpreter object: `0x492f90`
- Script parameter/buffer: `0x3be04a0`
- State pointer: `0x3bf1e40`
- Cursor pointer reported by observer: `0x0`
- Script prefix: `45 45 58 00 01 02 00 00 00 00 0e 00 00 00 01 00`
- State prefix: `60 1e bf 03 70 1e bf 03 80 1e bf 03 90 1e bf 03 a0 1e bf 03 b0 1e bf 03 c0 1e bf 03 d0 1e bf 03`

Observed handler opcodes: 9, 20, 28, 35, 48, 50, 51.
- Opcode 20 live cursor: `0x3be06b9`, cursor field `498`.

The observer hook records real process addresses and buffers. The first interpreter snapshot has a null pre-dispatch cursor, but the live opcode-20 handler supplies a valid cursor pointer and field. This is the runtime layout needed to replace the earlier incomplete synthetic object.
