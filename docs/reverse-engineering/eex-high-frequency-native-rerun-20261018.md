# EEX high-frequency native rerun

Native high-frequency handlers passed all mode cases for opcodes `9`, `52`,
and `51`. The probe also reconfirmed opcode 52's low-16-bit `0x8000` sentinel
boundary. Effect/resource selection passed `2560/2560` cases, with missing-key
commits equal to zero.

Machine outputs:

- `analysis/native-eex-high-frequency-validation.json`
- `analysis/native-eex-effect-dispatch-validation.json`
