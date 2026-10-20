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

Granting now has separate native evidence: **918/918** calls to `0x40DA45`
cover IDs 87..103, stock 0/1/98/99/100/255, money 0/999998/999999 and
controlled resale prices 0/10/255. Below 99 the count increases by one and
money is unchanged; at or above 99 stock remains unchanged and resale value
is added, capped at 999999. The price getter is controlled, while capacity,
stock writes and money helpers remain original. These deliberately invalid
stock values document the leaf behavior rather than normal inventory rules.
`grantNativeConsumable` matches every result. Reproduce with
`python tools/verify_consumable_grant_native.py`; raw evidence is
`native-consumable-grant.json`. Full opcode61 execution remains separate.

An additional **306/306** cases now execute original DATA item loading,
grant, capacity check, real resale getter and money helpers together with
no patched leaf functions. All 17 original consumable IDs cross the same
six stock and three money boundaries. The composed Web resale/grant rules
match every final stock, money and return value. This removes the controlled
price-leaf limitation for this original-item composition, while still not
claiming complete opcode61/UI execution or campaign stock initialization.
Reproduce: `python tools/verify_real_consumable_grant_native.py`.
Evidence: `native-real-consumable-grant.json`.
