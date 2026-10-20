# Item animation pixel blend

The native item loop invokes `0x42FD5A` for parameters 0..15, invert=1,
strength=0 and current palette. A new suspended-process capture executes
the original function with source indexes 0..255 and synthetic backgrounds.
Native lookup builder `0x42FCC6` remains live using Spalet entry 31. The
captured lookup and 4,096 output pixels are bundled in
`native-item-blend-frames.json`; destination guard bytes remain intact.

Web `nativeItemBlendPixel` independently matches every output. Source index
zero preserves background. Other pixels blend four-bit palette channels
with background weight frame*16 and source weight 256-frame*16, truncate,
then quantize through the native lookup. Frame zero still quantizes source;
this is not equivalent to browser alpha fading arbitrary RGBA images.

This proves the item-specific pixel loop, not full draw ordering, scene
palette setup or animation timing. Static `0x41C762` first draws the item
raised by 16 pixels with wait 5, then at the actor origin with wait 10, then
uses the 16-frame target loop with wait 1 per frame. Exact visible timing
still requires native scheduler correlation, rather than assuming easing.

Reproduce: `python tools/capture_item_blend_native.py` in reverse workspace.

Spalet 31 contains 738 source bytes; this probe explicitly pads its remaining
30 palette bytes with zero before installing the controlled 768-byte native
palette. Thus tail-index results prove the helper under that supplied palette,
not the game's actual palette initialization for those indexes. The earlier
short-buffer capture was discarded and rerun with the explicit padding.
