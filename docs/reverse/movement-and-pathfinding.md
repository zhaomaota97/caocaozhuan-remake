# Movement and Pathfinding Evidence

`analysis/movement-directions.json` is the native eight-neighbor table at executable RVA `0x8DF68`:

| index | dx | dy |
|---:|---:|---:|
| 0 | 0 | -1 |
| 1 | 1 | 0 |
| 2 | 0 | 1 |
| 3 | -1 | 0 |
| 4 | 1 | -1 |
| 5 | 1 | 1 |
| 6 | -1 | 1 |
| 7 | -1 | -1 |

`tools/verify_movement_table_native.py` decodes the movement table from `DATA.E5`, then invokes the original native movement-class and terrain-cost functions. The validation covers 53 unit classes × 30 terrain types = 1,590 cases, all matching (`analysis/native-movement-table-validation.json`). Impassable terrain is represented by cost `255`; an equipped movement modifier reduces every passable cost to `1` in the tested native path.

The live movement entry is RVA `0x38308`. Its hook records destination coordinate, budget, flags, start coordinate and mode whenever the UI reaches it; the current battle click test has not yet reached this entry because the battle view is a scrolling viewport.
