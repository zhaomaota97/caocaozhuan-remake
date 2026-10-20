# Promotion and experience item controller order

This is static Ghidra pseudocode evidence, not dynamic controller validation.
It corrects any assumption that a promotion only increments class ID.

Promotion category 76 executes `0x41D4DB`:

1. Select target through `0x45533D`; cancellation exits before mutation.
2. Resolve unit and apply `0x41C4E9`; failure exits before presentation.
3. Execute item presentation `0x41C762`.
4. Read OLD class record's growth indexes 5 and 6 through `0x4095A0`.
5. Double each growth value, truncate to one byte, and pass to unit stat
   increment helper `0x406E17` for HP and MP maximum attributes.
6. Refill current actor HP/MP using maximum getters and native setters.
7. Invoke unit dialogue/presentation `0x45778F` and load old/new SPC art.
8. Change class through `0x40DFF0` with old class plus one.
9. Run presentation/sounds, compare spell learnability for old/new class,
   dispatch notifications, then refresh actor animation.

The refill appears before the class setter. Whether changing class adds
further derived-attribute or equipment effects must be established from
`0x40DFF0` and a controlled full controller probe. Do not move operations
or assume class-independent maxima based solely on this ordering.

Experience category 75 executes `0x41D3D9`: target selection and eligibility,
item presentation, read stored XP through `0x406650`, add item base byte,
call `0x408950` with display enabled, then refill actor HP and MP from the
resulting unit maxima. Existing non-presentation growth tests do not prove
this full display-enabled controller or its learned-spell notifications.

Sources in the reverse workspace:
`analysis/native-main/pseudocode/0041d4db.c`, `0041d3d9.c` and `0041c4e9.c`.
The corresponding Web item actions remain incomplete; no guessed promotion
or experience-item mutation is enabled by this report.

Numerical helper sequence now has dynamic evidence: 477/477 calls using all
53 original class records and near-cap HP/MP base attributes match. Original
class loader, growth getter, stat increment and class setter execute without
replacement. This runs the state sequence reconstructed from the controller,
NOT the controller itself. It does not exercise refill, presentation, new
spells, inventory or eligibility; invalid promotion classes are deliberately
included only to test helpers. `0x40DFF0` itself only writes unit byte +0x2B.
Readable helper: `src/rules/promotionNumericalState.ts`; evidence:
`native-promotion-state-sequence.json`. Reproduce in the reverse workspace:
`python tools/verify_promotion_state_sequence.py`.
