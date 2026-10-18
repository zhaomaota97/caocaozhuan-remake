# EEX dialogue and target boundary rerun

Available native checks were rerun:

- Opcode 20 dialogue parsing: `11/11`
- Opcode 9 wait timer: `5/5`
- Low-frequency handler cases: passed
- Conditional handler cases: passed
- Opcode 48/50 missing-parameter early-return boundaries: passed
- Opcode 50 missing/non-type4 target boundary: passed
- Opcode 48 target ABI/boundary case: passed

The requested `verify_eex_dialogue_animation_commands_native.py` file is not
present in the current tool set; animation command behavior is covered by the
existing `verify_eex_animation_commands_native.py` (`970/970`) and is not
counted twice.
