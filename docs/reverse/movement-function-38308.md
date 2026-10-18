# Native Movement Function `0x438308`

Source: `analysis/native-main/pseudocode/00438308.c` (Ghidra pseudocode). Signature:

```c
byte __thiscall move(
    void *this, byte *start_xy, uint budget, uint flags,
    byte mode_a, byte mode_b, int restriction_mode);
```

The function uses the global battlefield dimensions (`DAT_004b422c`, `DAT_004b422d`) and a per-cell byte cost/occupancy buffer. It initializes the start cell, then repeatedly scans all cells at the current wave cost and expands the eight direction entries from `analysis/movement-directions.json`. Each candidate is rejected when its terrain cost is `0xff`, when the accumulated cost exceeds `budget`, or when the occupancy/faction restriction fails.

Observed flag behavior from the pseudocode:

| Flag | Effect |
|---:|---|
| `0x02` | Return the occupant/unit ID when the destination cell matches the target predicate |
| `0x04` | Build/update the reachable-cost map and refresh the selected-unit candidate list |
| `0x08` | Apply the special linked-cell/faction check before accepting a cell |

The routine calls `0x43F7CF` for terrain movement cost, `0x437D59` for the restriction predicate, `0x43B420` for coordinate/target matching, and `0x4359F5` for each directional neighbor. It returns `0xff` when no accepted destination is found, `1` for the flag-2 target hit, or a linked occupant ID for the flag-8 result branch. This explains why the earlier UI click test did not necessarily produce a move: the click must first select a valid actor and then pass the routine's target/restriction predicates.

The static function has callers at `0x4337F4`, `0x433BC8`, `0x43A7C9`, `0x43AD1C`, and `0x43D538`; these callers supply different flag combinations for reachability previews, target selection, and committed movement.

Caller-specific evidence from the recovered pseudocode:

| Caller | Calls observed | Role indicated by flags |
|---|---|---|
| `0x43A7C9` | `flags=8`, then `flags=2`, then `flags=4` | Find a reachable target, test target hit, then commit/update reachability |
| `0x43AD1C` | Same `8 -> 2 -> 4` sequence plus `flags=0` fallback | UI/AI target selection with a no-restriction fallback |
| `0x4337F4`, `0x433BC8` | Dynamic budget and mode values, followed by global refresh | Recompute reachable map after an action/state change |
| `0x43D538` | `flags=0` with zero initial budget | Reset/rebuild movement state |
