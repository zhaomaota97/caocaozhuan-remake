# Combat Resolution Pipeline

Static chain recovered from `004404bd.c`, `0043b50d.c`, and `0043bfaa.c`:

1. `FUN_004404bd(this, action_type, target_unit, effect_id)` selects the result branch. It renders the attack/effect frame through `0x450ED5`/`0x45119F`, then invokes the hit helper, magnitude function, status/effect functions, and finally commits the result animation.
2. Ordinary attack (`action_type=1`) calls `0x43BC4B` for base effect data and `0x43B50D(this,1,defender)` for hit probability.
3. Skill/effect attack (`action_type=2`) calls `0x43BFAA(attacker, defender, attacker_unit, effect_id, 1)` for magnitude and `0x43B73F` for the result/status path.
4. Special effect (`action_type=3`) uses `0x43C548` for effect magnitude and the same result path.
5. Item/equipment effect (`action_type=4`) uses `0x43C42E`; its critical probability is set by `0x41C4E9` and reaches 100 when the 玉玺 passive predicate succeeds.

`0x43B50D` computes ordinary hit chance from attacker/defender stats and RNG, with explicit 0% and 100% branches. `0x43BFAA` computes magnitude from attacker stat, defender stat, tiers, effect ID and live/battle mode. The final rendering path writes the combat result into the battle overlay buffer before the state update, separating visual animation selection from numeric damage calculation.
