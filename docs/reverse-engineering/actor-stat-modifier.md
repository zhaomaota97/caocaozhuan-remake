# Actor attribute state modifier

Original function `0x43F54C` was executed directly in a suspended native
process. All 5,120 cases matched: 20 base-value boundaries and all 256 state
byte values. The process was never resumed into UI or sound playback.

| State byte | Result |
| --- | --- |
| 0, 1, 2 | floor(base * 7 / 10) |
| 3 | base |
| 4 through 255 | floor(base * 12 / 10) |

The byte is an attribute-specific actor field, not the shared status bitmask.
Actor runtime offsets are attack `+0x18`, defense `+0x19`, agility `+0x1B`,
luck `+0x1C`. Outer native getters `0x43F4FE`, `0x43F595`, `0x43F631`,
`0x43F67F` call this helper and then clamp to 400. That outer clamp is
statically established; the dynamic matrix executes the modifier leaf only.

Unit base getters add equipment contributions before applying the actor
modifier. Attack/defense unit getters clamp their sums to 400; agility/luck
unit getters clamp to 300 before the actor modifier. Equipment contribution
aggregation still needs migration, so current scenario snapshots must not
be passed through this helper again: they already contain native modifiers.

Reproduce in the reverse workspace:

```powershell
python tools/verify_actor_stat_modifier.py
```

Raw evidence: `native-actor-stat-modifier.json`. Readable Web rules:
`src/rules/actorStatModifier.ts`. Values outside the observed base domain
and uint32 overflow behavior are not covered by this implementation claim.
