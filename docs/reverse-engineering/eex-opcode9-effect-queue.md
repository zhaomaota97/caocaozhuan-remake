# EEX Opcode 9 Wait Timer: Correction

The earlier queue interpretation below is withdrawn. `0x4B1B18` is a tick
deadline. `0x403340 -> 0x42C45F` stores current clock plus delay;
`0x42C479` returns remaining ticks and `0x42F7F0` tests expiration.
`0x47EB97` is `GetTickCount()/50`, and `0x47EAC4` pumps one Windows message
using PeekMessageA, TranslateMessage and DispatchMessageA. Opcode 9 doubles
its input before setting the timer, so positive input means nominally 100 ms
per unit, subject to 50-ms quantization and scheduler/message processing.

`python tools/verify_eex_wait_timer_native.py` passes 5/5 cases (0/1/2/10/100).
Only clock and message-pump leaves are replaced; native arithmetic, deadline
write, expiration test and wait loop remain executable. At controlled clock
1000 the native loop performs input*2 pumps, ending at deadline 1000+input*2.
Zero neither waits nor alters the seeded deadline. Raw evidence is
`native-eex-wait-timer-validation.json`. Actual GUI dispatch, negative delays
and tick-overflow behavior remain outside this probe.

## Withdrawn Interpretation

Opcode 9 handler `0x415B0F` reads value tag 4. Missing input
`0x80000000` returns interpreter status 5; an available value calls
`0x42C522(value)` and returns 1. The target is a queue operation:

1. `0x42C4CB(value)` writes `value << 1` into the global queue/state object
   `0x4B1B18` through `0x403340`.
2. `0x42C4E0()` drains that object by repeatedly testing `0x42F7F0` and
   dispatching `0x47EAC4` until the queue reports empty.

The dynamic handler probe verifies both missing and available branches and
records the target call. The queue's actual event meaning and presentation
timing are not claimed: its target and drain leaves were replaced/recorded in
the probe rather than run as a full UI event cycle.
