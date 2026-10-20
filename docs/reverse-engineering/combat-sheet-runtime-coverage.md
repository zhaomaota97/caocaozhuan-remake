# Full combat sheet runtime coverage

The migrated bank contains 151 attack sheets (12 frames, 64x64) and 151
special-pose sheets (5 frames, 48x48). Previously the browser preloaded only
art IDs appearing in S_00 or save slot08; later scenarios could reference
valid exported sheets that were absent from the texture manager.

Preload now follows all 302 records in `combat-sheets-map31.json`. Browser
coverage checks every sheet and every declared frame's dimensions, while
the existing ordinary attack interaction still checks animation/audio/HP
writeback. This fixes runtime resource availability, not all animation logic.
The images are still map31-palette conversions; scene-dependent unit colors
and complete presentation timings are separate fidelity requirements.

Verify with `npx playwright test tests/combat-sheet-coverage.spec.ts tests/attack-interaction.spec.ts --reporter=line`.
