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
