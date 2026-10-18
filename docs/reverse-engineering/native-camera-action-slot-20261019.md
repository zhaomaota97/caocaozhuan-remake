# Camera caller slot mapping

The ordinary presentation path resolves the camera slot from the action
record, rather than from the attacker UI selection:

1. `0x405E03` iterates the target-slot array at action object `+0x10`.
2. For the current iteration it writes that byte to action object `+0x01`.
3. `0x405744` begins by assigning `action[1] = action[0x10]`, then reads the
   actor pointer at `action+0x0c` and its `+0x06/+0x07` tile pair.
4. It calls `0x455123(camera, targetX, targetY, action[1])`.

Thus ordinary attack presentation follows the currently processed target
slot. Multi-target actions repeat this chain for each entry in `+0x10`; the
camera is not centered on the attacker and is not a single end-of-action jump.

The automatic item paths `0x41CCDF` and `0x41CE3D` use the same camera call,
but their action object stores the selected actor slot at `+0x02`; the exact
target/actor role for each item branch remains separately gated by the native
item predicate.
