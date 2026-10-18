# Combat Runtime Integration Scope

The battle scene now calls readable `src/rules/ordinaryExchange.ts` rather
than only showing deterministic damage. It composes the previously native-
verified hit/result/writeback/repeat helpers and category/range counter gate.
Critical presentation dialogue RNG consumption is placed before writeback.
Browser interaction verifies a real menu selection, attack/special sprite
playback, sound dispatch, HP mutation and acted state with no resource errors.
The exchange's primary result is compared against original executable fixtures.

Assets use actual map-31 palette and transparent index 0, exported by
`sanguozhi/tools/migrate_battle_combat_inputs.py`. Atlas source is UNIT_ATK
(three banks of four 64x64 frames) and UNIT_SPC (five 48x48 frames), not scene
PMAPOBJ sprites. Combat getter snapshots include attack, defense, agility and
luck for all 32 saved active actors. Terrain adaptation uses the current tile.

This is partial integration, not a full native-equivalence claim:

- Multi-target classes/equipment and automatic healing category 62 are rejected
  before RNG or battle mutation; their target/inventory lifecycle is unfinished.
- XP, equipment growth and recalculated statistics after growth are not yet
  integrated. The current attributes remain getter snapshots for this save.
- Animation uses the native attack bank and event tick sequence, but projectile,
  critical palette/flash effects, evade displacement and death lifecycle are
  not fully restored. Complete presentation equivalence is unverified.
- Counter and repeat helpers have original native evidence individually; the
  complete browser exchange is not yet compared to a full native controller trace.
- RNG follows the original generator and is stored with browser battle state.
  Initial seed 0 matches the observed startup setter; it is not a recovered
  mid-session random state from the original save.
- Turn progression, enemy AI, victory/defeat and strategy/item actions remain
  incomplete. The browser test relocates a real saved enemy to make an adjacent
  exchange testable; the default battlefield still uses original coordinates.

Tests: `tests/attack-interaction.spec.ts`, `tests/ordinary-exchange.spec.ts`,
`tests/local-save.spec.ts`, and existing movement tests. Screenshots are emitted
under `test-results/` by the browser test and may be replaced on later test runs.
