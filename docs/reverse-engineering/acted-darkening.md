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
