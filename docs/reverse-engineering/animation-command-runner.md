# Native Animation Command Runner

## Integrated Native Movement

The current probe passes 480/480 snapshots with **no function replacements**.
It runs the original command runner, reader, sequence binder/stepper, bounds
helper, collision scan, tile lookup and view accessors against an 8x8 map.
The movement function is only observed with an entry hook; it is not replaced.
Two map variants are empty or contain blocking tile 0xF001 at (5,4).

Each command stream and interval is executed on both maps. Besides counters,
frames and offsets, the independent model checks actual x/y and direction.
For stream [north,east,end], north succeeds in both maps; east then succeeds
on the empty map but is blocked on the obstacle map. The frame still advances
in both cases. This establishes the composition of scheduling and collision,
superseding the previous 240-row test with a movement-failure callback below.
Final rendering, sound, outer scheduler timing and real file-backed map/stream
initialization remain unverified here.

`python tools/verify_animation_command_runner.py` compares 240 native state
snapshots against an independent Python transition model. All pass. The
original runner `0x42A361`, command readers, linear view accessor, frame
binder and frame stepper execute; only the movement query is replaced to
record the direction and return failure. No graphics output is tested.

The matrix uses intervals 0/1/3 and streams containing movement commands,
direction-only commands, 0xE0 payload and 0xEF termination. Twenty calls per
stream/interval compare return low word, counter, command offset, frame
index, frame value, direction and movement-query arguments.

Verified state rules:

- While counter < interval, increment counter and do not execute a command.
- Otherwise reset counter and execute at most one nonterminal command.
- Commands 0x00-0x07 advance the frame sequence and query movement with the
  low nibble. Failed movement leaves position/direction uncommitted.
- Commands 0x10-0x17 set direction without advancing the frame sequence.
- In this runner, 0xE0 merely advances offset by two; its payload is not used.
  This does not prove its meaning in every other consumer.
- If the command at the resulting offset is 0xEF, return 0xFFFF in the same
  call. The terminator itself is not consumed. Later calls continue to obey
  the interval gate before reporting termination again.
- Nonterminal/interval-wait return low word is zero. Upper return bits are
  not meaningful status fields and are intentionally excluded.

Thus the interval field is a count of runner invocations, not a wall-clock
duration. The outer scheduling frequency, actual movement/collision behavior,
rendered frames, sound and resource-backed command-stream construction remain
separate verification requirements.

Raw evidence: `native-animation-command-runner.json`.
