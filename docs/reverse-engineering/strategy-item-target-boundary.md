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
The item controller's complete target-shape field has not been recovered.
The Web item menu therefore no longer paints every grid cell as reachable.
That previous full-map highlight was unsupported by native evidence. Item
result mutation and the controller-specific target geometry remain open.

Readable Web relation helper: `src/rules/nativeTargetEligibility.ts`.
It only covers the verified relation-byte boundary; effect-specific status
predicates from `0x420422` are not silently treated as eligible.
