# Battle victory/defeat predicate chain

The termination helpers provide a concrete static state machine:

- `FUN_0044C658` scans actor slots `0x23..0x73` for status classes `3/4`,
  tests their resource/state pair at `0x3D04`, and falls back to
  `FUN_0044C8E6(5,...)`; it clears the corresponding state through
  `FUN_0044F840` when the predicate succeeds.
- `FUN_0044C74D` scans slots `0..0x23`, tests the pair at `0x3D08`, and then
  checks whether the player-side slots contain any status class `1/2`; it
  falls back to `FUN_0044C8E6(0,...)` and clears through `FUN_0044F880`.
- `FUN_0044C8E6` counts living actor records by faction/type. Modes `0..3`
  match exact faction; mode `4` groups factions `0/1`; mode `5` groups `2/3`;
  mode `6` matches any living actor. It supports both full-table and bounded
  coordinate scans.

This identifies the static victory/defeat predicate inputs and faction groups,
but the final dispatcher/result code and live end-state branch remain
unverified.
