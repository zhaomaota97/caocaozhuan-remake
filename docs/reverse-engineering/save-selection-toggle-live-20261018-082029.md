# Save selection toggle live trace

The double `-0x6C` probe reached `FUN_00464E1F` twice:

1. row `0`, current `-1`, table value `0`;
2. row `0`, current `0`, table value `0`.

This confirms the native callback's toggle behavior: the first callback selects
row 0, and the second callback sees it already selected and clears it back to
`0xFFFFFFFF`. No save confirmation modal appeared, so confirmation is driven
by a separate dialog command/interaction after selection rather than by this
toggle callback alone.

Raw evidence:
`analysis/live-startup-20261018-082029/events.jsonl`.
