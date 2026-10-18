# Attack experience award calculators

Reproduce: `python tools/verify_attack_experience_awards.py`.
Native comparison: 9,408/9,408 cases passed. Raw evidence is in
`native-attack-experience-awards.json`.

The probe directly executes `0x40379B` (unit award), `0x40397D` (weapon
award), and `0x403A85` (defender armor award). Their native level, item-type,
equipment multiplier and actor-flag getters remain live; no function in
these three calculation paths is replaced.

Let `delta = defenderLevel - attackerLevel`, `M` be the relevant unit's
experience multiplier returned by `0x4072BD`, and `enabled` be action
`+0x600 != 0`. The getters read native level byte `unit+0x2C` directly.

## Unit experience

If disabled, award zero. Otherwise:

| Result | Positive delta | Zero or negative delta |
| --- | --- | --- |
| HP damage less than target's current HP | min(100, 8 + 2*delta) | max(1, 8 + delta) |
| HP damage at least target's current HP | min(200, 32 + 8*delta) | max(10, 32 + 4*delta) |

For the lethal branch only, double this base if the defender's unit ID
matches the word read at `0x492F90+0x3D06`. Final award is floor(base*M/10)
using the attacker's multiplier. The test controls this field directly;
its broader scenario initialization is outside this probe.

This calculator uses HP damage for lethal classification. It does not
require positive HP/MP damage for the nonlethal award when enabled.

## Weapon and armor experience

Weapon award is zero if disabled or if the attacker's slot-0 item type,
as classified by `0x40681A`, is nonzero. The matrix compares a real
category-0 weapon against a real category-10 weapon. For type zero:

- Both HP and MP damage zero: base 1.
- Either damage nonzero, attacker level above defender: base 2.
- Either damage nonzero, attacker level at or below defender: base 3.

Multiply by attacker's M and divide by 10 with integer truncation.

Armor award does not check action `+0x600`. It is zero when defender actor
byte `+5` is nonzero. Otherwise its base is 1 for no HP/MP damage, 3 for
damage when attacker level is below defender, and 4 for damage otherwise.
It uses the **defender's** M, then integer division by 10.

## Test scope

Levels are independently selected from 1/2/9/10/20/49/50. The matrix varies
reward enabled/disabled, leader match/mismatch, actor byte `+5` 0/1,
HP damage 0/1/100 against current HP 100, MP damage 0/1, two weapon types,
and multiplier 10/20. Other equipment is cleared. Multiplier 20 is a
controlled accessory made by changing in-memory item 103 to category 31
with value 20; original Data.e5 is untouched. Native multiplier lookup
executes normally. Every calculation starts with RNG state 7 and leaves
it unchanged.

Static integration evidence in `0x405E03` shows unit and weapon awards
accumulate by taking the maximum of the existing action totals and the
current target's award, while armor awards are stored per target.
This aggregation is not dynamically tested here. Nor does this probe
verify unit level growth, actual reward writeback, all weapon types,
all experience equipment combinations or presentation. Equipment XP
writeback has its own separate native boundary test and report.
