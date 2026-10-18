# High-frequency EEX handlers: static semantics

These handlers are selected from the actual 117-file corpus by
`eex-opcode-usage.json`; this page records static pseudocode semantics only.

## Opcode 52 (`0x413567`)

The handler reads two interpreter values through `0x4183F7`: slot/tag 2 and
slot/tag 13. If either returns `0x8000`, it returns interpreter status 5.
Otherwise it calls `0x428B87((value2 | 0x1000), value13, -1)` and returns 1.
The first value is widened with a `0x1000` command-class bit before dispatch;
the second is passed as a signed 16-bit value. No direct global assignment is
present in this handler. The corpus contains 2,388 occurrences in 56 files.

## Opcode 9 (`0x415B0F`)

The handler reads interpreter slot/tag 4. On missing input (`0x80000000`) it
returns status 5; otherwise it calls `0x42C522(value)` and returns 1. The
corpus contains 2,263 occurrences in 58 files.

## Evidence boundary

The argument tags and failure return values come from the native handlers and
the shared cursor reader. The target functions `0x428B87` and `0x42C522`
perform the actual game-side effects and have not been replaced or executed
in a dedicated synthetic probe here. These entries therefore remain
static-only in the EEX coverage matrix; the report does not claim that the
effects are fully understood.
