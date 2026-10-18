# EEX handler native rerun

Additional handler-level native checks were rerun:

- Amount updates: `96/96`
- Animation commands: `970/970`
- Enemy setup: `24/24` contexts, `480` records
- Unit restoration: `288/288` contexts
- Unit count: `6144/6144`
- Common configuration: `252/252`
- Numeric predicates: `360/360`
- High-frequency handlers: all listed cases pass, including the opcode-52
  `0x8000` reader boundary
- Opcode 48/50 success branches: `18/18`

These checks strengthen handler semantics and side-effect boundaries. They are
recorded as handler-level native evidence and do not imply a complete story
playthrough across every opcode.
