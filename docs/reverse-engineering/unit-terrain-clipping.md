# Unit terrain clipping masks

Native unit drawing `0x45137C` reads the terrain at the actor coordinate and
clears pixels using `0x430A07` with MARK masks before drawing. For terrain
codes 9/10 the 48px/64px masks start at 0x27C0/0x4BC0; code 2 uses
0x30C0/0x5BC0; code 1 uses 0x39C0/0x6BC0; code 7 uses 0x42C0/0x7BC0.
Terrain-to-offset mapping is static native evidence, not inferred terrain
names. Terrain 13 has additional compositing outside these masks.

All ten actual MARK mask/size combinations were executed through original
`0x430A07`. All 32,000 output pixels match the Web helper: nonzero mask
pixels clear the source index to zero, zero mask pixels preserve it. Raw
mask bytes are independently checked against migrated `Mark.e5` in tests.

`data/mappings/unit-terrain-masks.json` exposes Boolean blocked arrays;
`src/rules/unitTerrainMask.ts` is the readable clipping implementation.
Native draw and actor-coordinate terrain queries were not executed in this
probe, and live Web movement/attack compositing does not yet use these masks.
This is not a claim that complete terrain occlusion is migrated.

Reproduce: `python tools/verify_unit_terrain_mask_native.py` in reverse
workspace. Evidence: `native-unit-terrain-mask.json`.
