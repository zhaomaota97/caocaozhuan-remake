# Low-frequency EEX opcode validation

`python tools/verify_eex_low_frequency_native.py` executes six self-contained
native handlers in a disposable Ekd5 process. All cases pass and the raw
result is `native-eex-low-frequency-validation.json`.

| Opcode | Handler | Verified behavior |
|---:|---|---|
| 10 | `0x415AD7` | Clears all 256 dwords in the supplied interpreter table through `0x4184D1`, returns 1. |
| 3 | `0x4112DF` | No-argument fixed return 6. |
| 12 | `0x4143A4` | No-argument fixed return 8. |
| 7 | `0x415C46` | Reads and clears pending global `0x4AE4C0`; returns 1 when set and 0 when clear. |
| 13 | `0x4143AE` | Calls native global refresh with argument 0 and returns 7. |
| 30 | `0x413EF1` | No-argument fixed return 2. |

## Conditional handlers

`python tools/verify_eex_conditional_handlers.py` verifies opcodes 14
(`0x415890`), 73 (`0x415795`) and 84 (`0x415771`) with the native condition
function forced false and true. All 6 branches pass: each handler returns 1;
false skips its side effect, while true dispatches native action 3, action 2,
or `0x4CC03` respectively. The handler bodies execute unmodified; only the
condition is controlled and side-effect calls are recorded. Raw evidence is
`native-eex-conditional-validation.json`.

The opcode 10 test fills all 256 entries with `0xA5A5A5A5`, then verifies
both entry zero and entry 255 are zero after the native call. Opcode 7 uses
the actual global and verifies its state transition. The handlers run with
the original executable code; no handler is replaced. This validates the
isolated operation, not the larger story state machine that chooses when to
dispatch these opcodes.
