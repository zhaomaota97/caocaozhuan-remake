# Battle control and serialization validation

The following native verifiers were rerun against the current executable and
fixtures on 2026-10-18:

| Area | Result | Evidence |
|---|---:|---|
| Turn transition callers | 6/6 | `verify_battle_turn_chain.py` |
| Battle overlay states | 3/3 | `verify_battle_overlays_native.py` |
| Battle save round trips | 1160/1160 | `verify_battle_save_native.py` |
| Ordinary save object round trips | 5120/5120 | `verify_save_objects_native.py` |

The turn-chain result confirms both transition callers enter movement setup,
read the movement budget, and refresh the battle view. The serialization results
are byte/field round-trip checks; they do not imply that every victory-condition
branch or complete UI save/load interaction has been dynamically exercised.
