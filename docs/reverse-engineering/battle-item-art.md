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
