# Cao Cao Zhuan Remake: reverse and migration status

This document separates shipped evidence from runtime behavior. A copied file
is not counted as an implemented feature until a browser or rule test verifies
its use.

## In the independent project

- Native raw resources: `.e5`, `.e5s`, `.eex`, WAV and extracted binary banks
  under `public/assets/native-extracted/`.
- Converted Web assets: maps, unit animations, attack/special effects, audio,
  portraits, UI images and minimap assets under `public/assets/`.
- Native unit snapshots: `S_00` through `S_57` under `data/scenarios/`.
- Native terrain index: `data/scenarios/native-terrain-index.json`.
- Readable reverse evidence: `docs/reverse-engineering/`.
- Resource integrity: `npm run manifest:resources` produces SHA-256 hashes for
  11,185 migrated assets, including indexed acted-animation variants and
  original MARK status icons.
- Source migration integrity: `npm run verify:source-migration` compares every
  native `.e5`, `.e5s`, `.eex`, WAV and data file in the original directory by
  SHA-256 against `public/assets/native-extracted/`.
- Independence check: `npm run verify:independent` scans runtime source/data
  and rejects original-directory paths.

## Runtime verified

- S_00 battle shell, native unit placement, opening dialogue/path trace,
  minimap, context menu, combat rules, critical chance, hit/damage rules,
  animation state and native discrete camera stepping.
- S_01 native unit loading.
- Generic native unit and terrain loading for S_02 and subsequent indexed
  scenarios, with S_02 browser smoke coverage.
- Native EEX common-state rules for opcodes 32, 58 and 103, portrait selection,
  dialogue section parsing, and common-state dispatch.
- Native unit/weapon experience award formulas and level-growth writeback rules,
  with copied dynamic validation matrices under `docs/reverse-engineering/`.
- Build and rule checks: `npx tsc --noEmit`, `npm run build`, targeted
  Playwright tests.

## Evidence migrated but not fully executable

- Complete EEX handler table and story files are present, but only verified
  common-state handlers and the S_00 observed trace are executed by Web code.
- All 58 unit datasets are present, but complete per-scenario event scripts,
  faction setup, victory/defeat tails and AI workflows are not yet wired for
  every scenario.
- Raw resource banks are present, while some converted resource selectors and
  palette timing still require native presentation validation.
- Save/load serialization evidence is present; the Web save feature remains
  intentionally last and is not claimed complete.
- Experience award and growth calculators are implemented as pure rules, but
  the full battle reward callback is not yet wired to mutate Web roster state.
- `attack-interaction.spec.ts` explicitly restarts map31/slot-08 before testing
  attack animation, combat audio, HP writeback and acted state.
- Equipment experience level/XP writeback is implemented as a pure rule with
  native validation evidence; notification rendering and battle callback
  integration remain separate.
- Attacker reward controller `0x405C6C` state writeback is implemented in
  `src/rules/attackRewardController.ts` and matches all 2,592 captured native
  cases. It adds stored unit XP before growth and independently updates slot-0
  equipment, including when unit growth is ineligible. Native presentation
  callbacks and the battle-scene invocation remain unimplemented.

## Known fidelity boundaries

Recent rendering integration now uses native indexed actor darkening,
phase-dependent status-bit-16 coloring, original MARK status icons and
ordinary idle terrain clipping. Separate native matrices and browser pixel
checks are linked in the corresponding reports. These do not prove complete
movement/attack compositing, special terrain13 rendering, real-time palette
transitions or the complete original UI. All new render checks are available
through `npm run test:render-rules` and included in `verify:all`.

Where native evidence is absent, the port leaves behavior data-driven or
explicitly deferred. It does not replace missing native semantics with custom
gameplay assumptions.
