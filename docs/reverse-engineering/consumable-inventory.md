# Consumable stock indexing and decrement

Native functions `0x40D9C4`, `0x40DB3E` and `0x40D955` were executed for
all byte IDs 0..255 and counts 0/1/2/254/255: **1,280/1,280** matched.
An isolated common-state object supplies stock bytes; no function in this
query/decrement path is replaced. No UI or sound starts.

IDs below 87 have no stock index and query as 255; decrement does nothing.
Other IDs map to `id - 87`, stock byte at common object `+0x26B+index`.
Decrement reduces a nonzero count by one and leaves zero unchanged. IDs
beyond the shipped catalog test arithmetic, not supported inventory items.
The Web helper requires an explicitly initialized stock array; it never
invents counts for absent scenario inventory.

Static dispatcher `0x41DC43` checks action success at `+0x1C`, then invokes
decrement only when its final argument is zero. Success is set at the end
of item presentation `0x41C762`. This ordering is static evidence here;
the automatic-bean probe separately executes success-gated decrement with
the presentation-success leaf controlled. Complete manual inventory/UI
interaction remains open.

Reproduce: `python tools/verify_consumable_inventory_native.py` in the
reverse workspace. Evidence: `native-consumable-inventory.json`.
