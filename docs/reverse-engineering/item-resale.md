# Native item resale value

Original loader `0x40C537` and getter `0x40C7A9` were executed for all 104
original item definitions at level parameters 0/1/2/3/9/255. All 624 results
match the Web formula. No functions in this path are replaced; the native
main thread is never resumed, with no UI/audio.

Runtime item byte `+0x12` is loaded from DATA item input byte `+0x13`.
Value 255 returns sentinel 65535 before other calculations. Otherwise value
is `priceByte * 75`; categories below 18 additionally multiply by
`((level & 255) + 1)` and divide by two with truncation. Other categories
ignore the level parameter. This helper is a resale getter, not a complete
shop price/permission implementation.

Consumable overflow grant `0x40DA45` calls this getter with parameter zero
before adding money through the capped money helper. The required original
price metadata is now bundled in `data/rules/native-item-prices.json`.
Special sentinel handling by shops remains separate from this numeric leaf.

Reproduce: `python tools/verify_item_resale_native.py` in the reverse
workspace. Evidence: `native-item-resale.json`.
