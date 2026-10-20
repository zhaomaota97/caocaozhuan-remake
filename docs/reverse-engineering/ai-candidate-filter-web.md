# AI candidate filter in Web battle turns

Native `0x437A04` filters candidates before score calculation. The verified
conditions are map bounds, occupied-cell validity, nonzero target HP and the
caller-selected opposing/allied relation. Candidate order is not itself the
final AI score; native `0x438A20` and `0x4395AE` remain separate open work.

`src/rules/aiCandidateFilter.ts` implements only this verified boundary and
uses the existing native slot-side grouping represented by Web unit sides.
Enemy turns now use the filtered candidates before their current nearest
candidate fallback. After movement they are filtered again and the target
must be in the native range geometry before an attack is attempted.

The browser tests cover dead, hidden, out-of-map and allied records and the
post-movement stale-target case. This does not claim complete native AI
scoring, strategy selection, or campaign turn execution.

`src/rules/aiCandidateSelection.ts` now implements the separate native
ordered-list selector. All 6,144 captured native records match its final
score and target when supplied the captured ordered candidate list and
controlled score-leaf returns. It truncates scores to eight bits, replaces
only on strict improvement, and leaves target 255 when no positive score
exists. Boundary tests also check equal-score order and termination at
invalid/sentinel slots; the invalid-list case is static evidence only.

This test does not re-create the candidate list: geometry/filter coverage
belongs to the original native probe. Web scene sorting still uses distance
and lexical tie breaks, so full original enumeration order remains pending.
