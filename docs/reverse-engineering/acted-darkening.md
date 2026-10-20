# Native acted actor darkening

Renderer `0x43EB1F` copies the current 48x48 actor tile. If both actor flag
bits 2 and 4 are present and current HP is nonzero, it calls `0x430480` with
amount 4 before drawing. This operates on actor flags +0x0D, not status +0x1E.

The transform leaves index zero unchanged. For every other pixel it subtracts
the amount from each four-bit current palette channel with a zero floor,
then resolves the result through the native quantization lookup. A browser
RGB multiplication tint is not equivalent. Current live Web tint remains an
approximation until exact indexed/darkened texture rendering is connected.

Direct execution of original `0x430480` and lookup builder, with palettes
0/31/57 and amounts 0/1/4/15, produced 3,072 output pixels. The Web pixel
rule and regenerated lookup match all outputs. Tail colors are explicit
zero-padding controlled inputs. The actor flag gate is static evidence here;
the probe does not execute the full renderer or status overlays.

Reproduce: `python tools/capture_acted_darkening_native.py` in reverse
workspace. Evidence: `native-acted-darkening.json`.

Live integration now replaces Web tint with indexed-darkened movement sheets.
All 58 scene lookups produce 55 distinct used-pixel RGBA profiles (8,305
movement sheets, deduplicated). Only the current scene's profile is loaded.
`nativeActorIsDarkened` controls the texture; frame and mirroring are retained
and RGB tint is cleared. Returning to unacted state restores the normal bank.
This supersedes the earlier live-tint limitation above.

`acted-movement-art.json` records scene/profile/sheet mappings. Browser tests
check texture selection and compare one entire 11-frame decoded sheet to
the reconstructed indexed transform using original raw Unit_mov pixels and
the independently verified native lookup algorithm. Existing attack playback
still passes. This is exact for the supplied scene palette, not full native
status overlay or rendering capture. Source colors may be shared while
darkening differs because quantization can select scene-specific terrain colors.
Generate with `python tools/export_acted_movement_art.py` in reverse workspace.

The actor gate now also has direct renderer evidence: all 256 flag bytes
crossed with HP zero/nonzero produce 512/512 matching original `0x43EB1F`
executions. Original action-mask/HP getters, darkening and lookup run. Only
the source tile provider and final draw are replaced; all 2,304 final tile
pixels are checked for each case (1,179,648 pixels total). The supplied tile
cycles every byte index, and expected dark pixels come from the native
darkening function in the same probe. Web predicate matches all decisions.
This supersedes the gate's earlier static-only limitation. Status flags are
zero, so it does not validate the status-color or status-icon branches.
Reproduce: `python tools/verify_acted_render_gate_native.py`.
Evidence: `native-acted-render-gate.json`.
