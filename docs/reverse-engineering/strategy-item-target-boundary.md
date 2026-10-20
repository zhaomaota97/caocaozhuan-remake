# Strategy and item target boundary

Native strategy target setup calls `0x436586` through `0x4391DC`; the range
selector is masked to seven bits and the native flags are passed separately.
The geometry implementation is validated in `target-geometry-flags.md`.
The outer target predicate `0x420422` also applies the effect record's
relation byte: relation 0 means opposing native slot groups, relation 1 means
the same group. The captured actor layout uses slot `<35` as the same group
boundary for the current battle records.

Manual item setup initializes through `0x41DBBC` and selects targets through
`0x45533D`, which invokes native geometry with controller-specific arguments.
The initializer explicitly writes range 1 to controller `+0x18`. Manual
handlers pass it to the selector with mode 4; `0x45533D` includes the origin
and requires matching faction groups for that mode. The earlier statement
that this range field was unrecovered was incorrect.

The Web now highlights shape 1 plus origin and rejects enemy, hidden, dead
and out-of-range item preview targets. It invokes native eligibility helper
`0x41C4E9`'s mode-zero equivalent for its supported category gates. The
geometry and eligibility helpers have independent native evidence; complete
UI-driven item selection/result/inventory flow remains unverified. Item
result mutation remains open, so these gates do not claim working item use.

Readable Web relation helper: `src/rules/nativeTargetEligibility.ts`.
It only covers the verified relation-byte boundary; effect-specific status
predicates from `0x420422` are not silently treated as eligible.
