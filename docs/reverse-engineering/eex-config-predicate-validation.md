# EEX configuration predicate validation

`python tools/verify_eex_config_predicates_native.py` executes native opcode
handlers 66 (`0x411D63`) and 67 (`0x411D8E`) with a controlled interpreter
object. The object is in mode 1, so both handlers use their direct script
slots rather than the scenario-global branch. Slots 5 and 6 point to a
controlled 32-bit value.

For values `0`, `1`, `2`, and `0xFFFFFFFF`, both handlers return exactly
`value == 1`. Each handler calls its own native configuration refresh once:
opcode 66 uses `0x44C658`; opcode 67 uses `0x44C74D`. The refresh functions
are replaced only to isolate the predicate and count calls; handler bodies
and slot reader `0x41004D` remain native.

The eight emitted rows and `passed: true` are stored in
`native-eex-config-predicate-validation.json`. This proves the interpreter
mode-1 slot predicate and refresh boundary. It does not prove the mode-0
global configuration scans or the story conditions that select these opcodes.
