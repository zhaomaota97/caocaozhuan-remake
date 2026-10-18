# EEX Handler Static Semantics Index

`tools/export_eex_handler_semantics.py` joins `analysis/eex/opcode-index.csv` with the recovered native pseudocode for each handler. The output is `analysis/eex-handler-semantics.json`.

The index covers all 108 opcode slots: 106 have handler pseudocode and 2 are reserved/terminal. For each handler it records classification, parameter tags, every recovered `FUN_XXXXXXXX` call, and global `DAT_`/string-symbol tokens referenced by the pseudocode. 60 handlers explicitly reference global state. This is the static baseline for completing opcode semantics without requiring a live story playthrough.

The index also records `suspected_global_writes`, extracted only from direct pseudocode assignments. Seven handlers have such direct writes: opcode 6 (`0x4B09EC`), 7 (`0x4AE4C0`), 39 (`0x4ABF9C`/`0x4B3D08`), 69 (`0x494FD0`, `0x496C94`, `0x496C96`, `0x496C98`, `0x496C9A`, `0x496C9F`, `0x496E21..23`), 91 (`0x4B3D10..17` subset), 93 (`0x4B3D0B`), and 106 (`0x4B3D10`). These are high-value candidates for side-effect-focused native validation.
