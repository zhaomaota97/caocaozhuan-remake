# Battle state transition table rerun

`tools/index_battle_termination_chain.py` was rerun against all 11 recovered
battle target/turn/termination routines. Every source body is present.

| Native routine | Static role | Global state evidence |
|---|---|---|
| `0x438A20` | target candidate scoring helper | actor table, map dimensions, target slot `0x4B2C50`, battle state `0x4B422C` |
| `0x438965` | attack-range candidate selection | candidate table `0x4AC748`, selected slot `0x4B2C30` |
| `0x4391DC` | effect/status candidate scoring | effect table `0x4AC7AC`, selected category `0x4B2C2C/40` |
| `0x4395AE` | per-candidate evaluation | actor/effect tables, target slot |
| `0x43A529` | aggregate best target/result | target coordinate `0x4B2C20`, score/category fields `0x4B2C28..44` |
| `0x43AD1C` | consume aggregate result / dispatch next state | result fields and `0x4B420C` |
| `0x4337F4` | player-turn refresh entry | movement/UI globals and battle state |
| `0x433BC8` | alternate turn refresh entry | movement/UI globals and battle state |
| `0x44C658` | termination-side state helper | actor/result table |
| `0x44C74D` | termination-side state helper | actor/result table |
| `0x44C8E6` | termination-side state helper | actor/result table |

The recovered chain shows target scoring feeding a shared result buffer, then a
dispatcher consuming that buffer. It still does not prove which result values
mean victory versus defeat: no live trace has reached the end-state dispatcher.
The machine index is `analysis/battle-termination-chain.json`.
