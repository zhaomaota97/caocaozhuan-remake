# Consumable restoration amount

Original helper `0x43C42E` matches 180/180 controlled native calls. The
matrix crosses categories 63/64/70, base bytes 0/1/30/254/255, maxima
100/250/500 and current values 0/1/99/maximum. Maximum HP/MP getters are
stubbed; the actual helper reads the actor current fields and item record.
The native process never resumes into UI or audio.

Categories 63/64 use HP/MP respectively. Value 255 returns the whole missing
amount; other values return the smaller of value and missing amount. Other
categories return the item base value. No percent calculation occurs here.
The Web helper rejects over-maximum states because the native unsigned
underflow boundary has not been probed.

Caller distinction from static native code: HP controller `0x41CCDF` adds
the full amount before max-HP clamping; MP controller `0x41CE3D` truncates
the amount with `&255` before adding it and applying max-MP clamping.
This caller detail is not dynamically tested by this helper probe. Normal
maximum MP is lower, but the truncation must not be silently discarded.

No complete item-use claim: inventory decrement, presentation, selection
and all result-controller branches remain separate. Reproduce in the
reverse workspace: `python tools/verify_item_restore_amount_native.py`.
Raw evidence: `native-item-restore-amount.json`.

Controller probe now adds **120/120** original executions. It calls native
initializer `0x41DBBC`, then HP controller `0x41CCDF` in self-target mode
or MP controller `0x41CE3D` with the target selector controlled to slot zero.
Original eligibility, amount and resource setters remain live; only maxima,
target selection, item presentation, camera and result display are controlled.
The full-amount HP and low-byte MP distinction above now has dynamic proof.
`nativeItemRestoreWriteback` matches every captured final HP/MP pair,
including deliberately expanded maximum MP 500 to expose byte truncation.
This does not prove normal gameplay allows that maximum, nor validate UI
presentation, external target selection or inventory decrement.
Reproduce: `python tools/verify_item_restore_controller_native.py`.
Evidence: `native-item-restore-controller.json`.
