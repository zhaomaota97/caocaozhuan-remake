# Repeated long EEX probe

An independent 60-second startup/new-game run was captured at
`analysis/live-startup-20261018-090840`. Rebuilding the aggregate live EEX
summary increased the run count from 17 to 18, while the opcode union remained
15 slots: `2,8,9,10,20,28,35,39,47,48,50,51,58,59,62`.

This confirms the current automated startup path is stable and reproducible,
but does not expand story branch coverage.
