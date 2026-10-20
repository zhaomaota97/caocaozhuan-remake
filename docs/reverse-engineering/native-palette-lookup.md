# Native palette quantization lookup

Web `buildNativePaletteLookup` reconstructs `0x42FCC6 -> 0x42FB10`. Every
one of its 4,096 generated entries matches the native map31 controlled-palette
capture. The item blend comparison now uses the regenerated table rather
than importing native output as the implementation's lookup input; all
4,096 blend pixels still match.

For each four-bit color, the search considers palette indexes 10..245 only.
The strongest channel is the first strictly highest channel (default zero).
Candidate and input strongest-channel positions must match. A candidate
replaces the previous choice only if both maximum absolute channel difference
and sum of absolute differences are no worse. Exact ties therefore choose
the later index. No eligible candidate leaves output zero. This is neither
Euclidean nearest-color selection nor a simple lexicographic error sort.

Extra synthetic boundary tests for reserved indexes and ties are based on
static code; they are not new native synthetic executions. Dynamic proof
currently uses the captured map31 palette. Palette tail indexes 246..255
cannot enter lookup candidate selection, narrowing the prior tail concern.
They can still affect the background-channel inputs to pixel blending.
The real scene palette initialization and full item render remain open.
