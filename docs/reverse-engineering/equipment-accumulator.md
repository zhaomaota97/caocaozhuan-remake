# Complete equipment attribute accumulator

Native `0x407C0E` was executed for 2,600 controlled loadouts and all nine
attribute selectors: 23,400 comparisons matched. Coverage includes every
original item alone in every slot, repeated three-slot items, mixed items,
and stored levels 0, 1, 3, 9 and 255. The harness keeps the original item,
class and unit loaders active in a suspended process.

Slots 0 and 1 add level-adjusted contribution when the primary category
matches. For odd weapon/armor categories below 18, a matching secondary
effect adds its separate value. Slot 2 adds only the base primary value.
The result wraps to eight bits, rather than saturating at 255.

Selector mapping: attack 0, defense 1, intelligence 2, agility 3, luck 4,
HP 5, MP 6, movement 7, experience multiplier 8. This mapping follows
the native category dispatch and unit getter call sites.

`nativeBattleAttributes` combines this accumulator with the native unit
getter caps and actor state modifier. Recalculation from raw unit/actor
bytes matched all exported actor getter snapshots across 58 scenarios.
The live Web scene now recalculates the four combat attributes from each
unit's current equipment instead of reusing the final getter snapshot.
Slot-08 saved actors still use their separate saved-state snapshots.

Remaining limits: base stats and attribute states are initialized from
scenario captures; full unit-growth and temporary-state controller
writeback is not yet connected. Only the four combat getters are exposed
by this combined helper. Campaign setup is the controlled default party,
not an unmodified complete campaign playthrough.

Reproduce native evidence in the reverse workspace:

```powershell
python tools/verify_equipment_accumulator.py
```

Web evidence: `npm run test:actor-stats`; raw native results are in
`native-equipment-accumulator.json`. The S_01 browser test checks every
living actor against native values and changes an equipped weapon's stored
level to confirm that live attack attributes are recalculated.
