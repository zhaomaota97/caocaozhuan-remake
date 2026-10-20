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

The test now independently generates the candidate list with
`collectNativeAdjacentCandidates` before selection. All 6,144 lists and
selected results match native outputs for shapes 0/1, including map corners,
group masks and HP masks. Shape 1's diagonal occupancy is absent from the
captured matrix; diagonal order is supported by the original constant table
and static call sequence, with a separate Web test rather than claimed
dynamic diagonal validation. Other ordered shapes throw explicitly.

Web scene sorting still uses distance and lexical tie breaks. The ordered
shape collector is not yet connected to complete movement-cell selection;
this report does not claim full native AI turn fidelity.

The diagonal coverage gap above has now been probed directly: native shape
1 with units in all eight neighboring cells passes 216/216 controlled cases.
These vary side/HP masks, tied and byte-overflow scores, center and corner
origins. Web generation and selection independently match all 216 native
lists and winners. The original score leaf and resource buffers remain
controlled; this does not validate complete AI scoring or campaign turns.
Reproduce in the reverse workspace with
`python tools/verify_ai_diagonal_candidates_native.py`. Raw evidence:
`native-ai-diagonal-candidates.json`. No native UI or sound was started.

Battle integration now uses the ordered collector and selector for the
post-movement ordinary target choice when the attack shape is 0 or 1.
Candidates are generated at the actor's actual position, then scored with
the current ordinary-score inputs. Ties retain native enumeration order;
all-zero scores leave no attack target. This replaces global score/distance/
lexical sorting for that specific stage and those two shapes. The movement
destination selector, pre-movement approach target, other shapes and effect
AI still use incomplete workflows and must not be described as original AI.
