# Actor status indexed-color overlay

Native renderer `0x43EB1F` applies `0x43053E(tile,48,48,4,8,4)` after acted
darkening when status byte +0x1E has bit 16 and `(phase & 3) > 1`.
Phase is returned by `0x41C2D0` from object byte +5. These gates and ordering
are static renderer evidence; this probe runs the actual pixel functions.

Parameter-to-channel ordering is 3/1/2, so renderer values 4/8/4 subtract
6 from the first two four-bit palette channels and add 2 to the third,
clamping at 0 and 15, then quantizing through the native lookup. Index zero
is preserved. When acted darkening also applies, its quantized output index
becomes the input of the status transform; merging RGB adjustments before
quantization is not equivalent.

Original lookup builder, darkener and status-color function were executed
on source indexes 0..255, with/without darkening, for palettes 0/31/57.
All **1,536** output indexes match Web composition. Palette missing tails
are explicitly supplied as zero; actual live palette initialization remains
separate. No native UI/audio was started. The live Web renderer does not yet
apply this phase-dependent state overlay; no generic tint substitutes for it.

Reproduce: `python tools/capture_actor_status_color_native.py` in reverse
workspace. Evidence: `native-actor-status-color.json`.

Live Web integration now generates and caches movement-sheet canvas textures
from migrated raw Unit_mov pixel arrays and readable scene palettes. It
rebuilds the native lookup, optionally applies acted darkening, then applies
the status transform. Per-phase updates switch between cached status and
normal/acted sheets, retaining frames and mirroring; no generic tint is used.
This supersedes the earlier live-renderer limitation for status bit 16 color.
The browser test verifies phase switching, acted composition and nonblank
canvas pixels; native pixel correspondence remains covered by the separate
1,536-output matrix. The native global phase clock has not been fully
correlated to wall time; Web uses its existing animation phase source.

`data/mappings/scene-palettes.json` preserves four-bit source channel order
with explicit zero-filled unused tails. These inputs do not reconstruct all
live preceding-palette transitions. Generate that readable data with
`node tools/build-scene-palettes.mjs`. Other status overlays/icons remain open.
