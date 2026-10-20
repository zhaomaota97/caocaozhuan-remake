# Native idle phase cadence

Original idle wait controller `0x455CB2` was executed with deterministic
clock and input callbacks and rendering suppressed. Fifteen cases cross
initial phase 0/7/255 and input termination after 1/8/9/17/25 ticks. All
native phase updates, redraw timestamps and final timer deadlines match.
Original `0x406730`, `0x42C4CB` and deadline helpers execute normally.

This controller starts a wait of 4 through the doubling wrapper, giving
8 native 50ms ticks (400ms). Each expiration advances phase as `(phase+1)&7`,
redraws, and resets the deadline. Immediate input exit does not advance phase.
The Web idle cadence now uses this documented constant rather than reading
a hardcoded duration from the slot08 save export.

This is not proof of a universal global animation clock. Target-selection
loop `0x4541A9` additionally gates progression on viewport/input conditions;
attack and strategy controllers call the increment helper at explicit
presentation points. Web still lacks all of these event-driven updates.
The probe does not establish real-time draw latency or full gameplay timing.

Reproduce: `python tools/verify_idle_phase_wait_native.py` in reverse
workspace. Evidence: `native-idle-phase-wait.json`.
