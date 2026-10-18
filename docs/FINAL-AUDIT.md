# Final reverse-engineering audit

This is an evidence index, not a completion claim.

| Requirement | Evidence | Current state |
|---|---|---|
| Native executable/DLL analysis | `docs/reverse-engineering/` call graphs, pseudocode extracts and DLL reports | Evidence bundled; full semantic labeling remains open |
| `.e5`/map/resource extraction | `public/assets/native-extracted/`, converted `public/assets/`, `RESOURCE-MANIFEST.json` | Bundled and hash-verified |
| All scenario unit/terrain data | `data/scenarios/S_00..S_57-*`, `native-terrain-index.json` | Integrity-tested; S_00/S_01/S_02 runtime-tested |
| Movement/attack/combat formulas | `src/rules/`, native fixtures and `test:reverse-rules` | Verified rule coverage; complete campaign integration remains open |
| EEX format and handlers | `src/rules/eex*`, `data/mappings/eex-*`, `docs/reverse-engineering/open-work-items.md` | Verified subset executed; 78 opcode slots remain static-only |
| UI, dialogue, portrait, camera, sound and animation | `BattleScene.ts`, native fixtures, targeted Playwright tests | Key paths verified; full UI event/sound correlation remains open |
| AI turns and complete battle flow | native reports and S_00/S_01 tests | AI full-turn trace and all scenario event tails remain open |
| Save/load | save format reports and raw `.e5s` resources | Native codec evidence present; Web save/load intentionally unfinished |
| Independent local operation | `npm run verify:independent`, only `5173` service | Passed; no runtime source-directory dependency |
| Resource integrity | `npm run verify:resources` | 2772 files hash-verified |

The project remains intentionally incomplete where native evidence or an
unmodified dynamic trace is missing. Those boundaries are recorded rather
than replaced with invented gameplay behavior.
