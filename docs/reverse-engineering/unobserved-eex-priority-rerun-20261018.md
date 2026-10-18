# Unobserved EEX priority list

Using the 15-opcode live union and the complete static handler index, the new
priority tool ranks 91 non-reserved handlers not yet seen dynamically. The
score favors global writes, native calls, and explicit parameter readers.

Top candidates are opcode `69` (score 34), `61` (29), `107` (29), `76` (27),
`92` (27), `57` (25), `82` (25), `91` (24), `89` (21), and `56` (19).

Machine output: `analysis/unobserved-eex-priority.json`.
This is a scheduling aid based on static evidence; scores are not gameplay
semantics and no unobserved opcode is claimed dynamically verified.
