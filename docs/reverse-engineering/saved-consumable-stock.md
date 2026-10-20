# Actual saved consumable inventory

All ten original `Sv00d..Sv09d.e5s` common records were loaded with native
`0x40CC65` and queried through `0x40DB3E` for IDs 87..103. All 170 counts
match the original file bytes. The loader consumes 654 common bytes. Stock
starts at common input offset 637, file offset `0x32+637 = 0x2AF`, and maps
to runtime common object `+0x26B` for 17 consecutive bytes.

The common prefix contains 16 bytes, two sets of five uint16 fields, one
byte, then 200 three-byte equipment entries. The stock array follows those
600 equipment bytes. This explains the on-disk/runtime offset distinction.

Readable counts are bundled in `data/saves/consumable-stock.json` and tested
against independently migrated raw save files. These are actual saved
inventories, not new-campaign or per-scenario initial inventories. No default
stock is supplied for missing campaign state. Save writing remains deferred.

Reproduce in the reverse workspace:
`python tools/export_saved_consumable_stock.py`. The process stays suspended,
with no native game UI or sound.
