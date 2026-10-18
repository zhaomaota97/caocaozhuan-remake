# Native manual item controller boundary

Native entry `0x41DC43(this, itemId, targetSlot, param3, param4)` initializes
an item action through `0x41DBBC`, reads the item's category byte from the
native item table, then dispatches by category:

| category byte | native controller | current Web status |
|---:|---|---|
| `0x3F` (63) | `0x41CCDF(this, param3)` | automatic/manual bean path evidence only |
| `0x40` (64) | `0x41CE3D(this)` | native path identified, result not migrated |
| `0x41..0x45` | `0x41CF61(this)` | controller not migrated |
| `0x46..0x4A` | `0x41D080(this)` | controller not migrated |
| `0x4B` | `0x41D3D9(this)` | controller not migrated |
| `0x4C` | `0x41D4DB(this)` | controller not migrated |

After a controller sets action `+0x1C` nonzero, native decrements inventory
through `0x40D955` when `param4 == 0`, then refreshes both the target and item
owner through `0x479A01`. This confirms that category `63` is a real manual
item dispatch as well as the separately verified automatic recovery path, but
does not by itself establish the UI target restrictions or inventory state
needed for a faithful Web implementation.

The Web port therefore keeps manual item result mutation disabled until the
corresponding controller and inventory preconditions are verified. Equipment
categories and consumable categories remain separate.
