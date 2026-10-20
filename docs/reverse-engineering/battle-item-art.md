# Battle item image bank

All 104 `ITEM.E5` entries are exported to
`public/assets/effects/items-map31/item-000..103.png`. Each original entry
is exactly 1,024 indexed pixels, rendered at native 32x32. Source index zero
becomes alpha zero; other indexes remain fully opaque. Each saved PNG is
decoded and compared byte-for-byte with the expected RGBA buffer by the
exporter. Index and RGBA SHA-256 values are retained in
`data/mappings/battle-item-art.json`.

These are battle-use images, distinct from Itemicon.dll inventory/treasure
icons. Native presentation `0x41C762` selects ITEM.E5 by item ID and draws
32x32. The export uses the already established Spalet entry 31 conversion
(channel order 1/2/0, high nibbles). It is explicitly map31 art, not a claim
that every scenario uses that palette or that item animation is complete.

Reproduce in the reverse workspace: `python tools/export_battle_item_art.py`.
Browser coverage decodes all images, checks dimensions and visible pixels.
Exporter RGBA checks prove palette conversion consistency, not independent
pixel equivalence to a captured native item animation.

Subsequent native wrapper evidence in `short-palette-tail.md` proves short
palette records preserve and shift the previous tail. This zero-padded PNG
bank is therefore an explicit preview assumption for tail indexes 246..255,
not a universal native palette load. A live preceding-palette capture is
still needed before claiming exact campaign colors for those indexes.

Exact resource audit now narrows this boundary for ITEM art: all 104 images
(106,496 source pixels) use indexes no higher than 173. None references
246..255. `item-palette-coverage.json` checks original ITEM index counts
against each Spalet record length; map31 has no missing used source colors.
Thus zero padding does not alter the source colors of these specific ITEM
images. It can still affect background colors and native quantization lookup,
so complete blended scene pixels are not proven independent of prior state.
Reproduce: `python tools/audit_item_palette_coverage.py` in reverse workspace.
