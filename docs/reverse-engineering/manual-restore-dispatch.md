# Manual restoration dispatcher and inventory gate

Native `0x41DC43` was executed in 48 combinations: categories 63/64,
stocks 0/1/2, normal/free-use flag, selected/cancelled target, and controlled
presentation completion. Original initializer, restoration controllers,
eligibility, amount, resource setters and stock decrement remain live.
Maxima, target selector, presentation, camera, display and refresh leaves
are controlled. All 48 outputs match the Web state-path helper.

Selection returning 255 leaves resources/stock unchanged and returns zero.
With a selected eligible target, restoration runs. Final stock decrement
only occurs when controller success is nonzero and free-use is zero; stock
zero remains zero. This dispatcher does not itself reject zero stock: the
normal inventory/UI caller must do that before dispatch.

The presentation callback sets success in the real code. If this probe
suppresses that assignment but returns normally, restoration still runs,
while stock and return-success remain unchanged. This artificial boundary
does not prove actual UI animation cancellation/failure behaves that way.
The Web helper preserves the measured ordering and is not yet called by
the live item preview until inventory initialization and presentation flow
are connected. MP category here deliberately uses controlled item 87 with
a changed in-memory category; original files are never modified.

Reproduce: `python tools/verify_manual_item_dispatch_inventory.py` in the
reverse workspace. Raw results: `native-manual-item-dispatch-inventory.json`.
