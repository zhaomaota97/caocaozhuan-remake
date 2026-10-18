# EEX high-frequency handler boundary validation

`python tools/verify_eex_high_frequency_handlers.py` executes native handlers
9 and 52 with the shared reader and target effect calls instrumented.

Opcode 9 passed both synthetic reader branches: missing input returns status
5 without calling `0x42C522`; available input returns 1 and calls
`0x42C522(value)`. This validates the handler's failure/success boundary, not
the target effect itself.

Opcode 52 now passes both synthetic reader branches: low-16-bit sentinel
`0x8000` returns status 5 without calling `0x428B87`; available inputs return
1 and call `0x428B87`.
The recorded calls show the expected command-class bit (`0x1000`) in the
first argument and signed/16-bit-looking values in the remaining arguments.
The first failed attempt used `0x80000000`, which was wrong because the
handler compares the low 16 bits. The corrected probe uses `0x8000` and
reaches the native failure branch. This also documents a calling/data-width
detail needed by future cursor decoders.

The same probe now covers opcode 51: missing values return 5; available
values return 1 and call `0x428B87` with the third reader value forwarded as
the third short argument. This confirms that opcode 51 and 52 share the
effect-table target while differing in parameter-3 source.

Raw results are in `native-eex-high-frequency-validation.json`. The test
passes only the evidenced assertions and preserves the opcode-52 limitation.
