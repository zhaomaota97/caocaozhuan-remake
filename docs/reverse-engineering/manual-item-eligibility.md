# Manual item eligibility

Direct native `0x41C4E9` execution matches **13,328/13,328** decisions using
actual item definitions for categories 63..76. The matrix crosses modes 0/1,
seven status bytes, eight class boundaries and levels 1/14/15/29/30/49/50.
Only error notification `0x42F699` is suppressed; original field getters
remain active. The native process is never resumed into UI/audio.

Check mode (nonzero) requires status bits 8/16/2/4 for categories 65/66/67/68,
and any status byte for category 69. Mode zero skips those tests. Category
75 always requires level below 50. Category 76 always requires class below
39, class modulo three not equal to two, and level at least 15 or 30 for
class modulo three zero or one. Other categories pass this leaf.

This is one eligibility helper, not complete eligibility: target range,
faction, life/type, inventory availability and effects are separate. It is
not yet wired to the incomplete Web item preview as a complete controller.
Readable rule: `src/rules/manualItemEligibility.ts`. Raw native evidence:
`native-manual-item-eligibility.json`. Reproduce in the reverse workspace:
`python tools/verify_manual_item_eligibility.py`.
