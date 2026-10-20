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

Full draw-wrapper evidence now adds 14/14 executions of original `0x45137C`
at sizes 48/64 and terrain inputs 0/1/2/7/9/10/255. Terrain query, resource
buffer accessor and final draw are controlled; the original branch selection,
tile copying and mask application remain active with actual MARK bytes.
Every selected buffer offset and final tile pixel matches the Web mask data
and helper. This supersedes the static-only mapping limitation above for
these branches, not actual actor-coordinate queries or special terrain13.
Reproduce: `python tools/verify_unit_terrain_draw_native.py`.
Evidence: `native-unit-terrain-draw.json`.

Live idle movement-sheet rendering now clips the recovered 48px mask types
after darkening/status coloring, using terrain at the actor's current tile.
Canvas textures are cached by art, scene, color state, terrain and mirror
setting. Frame banks mirrored by Web sprites sample the mask in reverse so
the final clipping remains fixed in world coordinates, rather than reflecting
the terrain mask with the actor. Browser tests compare entire decoded sheets
for ordinary and mirrored actors against original indexed pixels/mask bytes.
The mirrored-bank composition follows the separate established frame-mirror
rule; native full mirrored render captures remain a further validation step.

This supersedes the lack of idle Web integration above. Movement presentation,
64px attack rendering and special terrain13 compositing remain incomplete.
Status icons are drawn after the actor and are not cropped by the tile mask.
