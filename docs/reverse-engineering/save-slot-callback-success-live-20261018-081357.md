# Save slot callback success live proof

After changing the synthetic list item state to focused+selected (`state=3`,
`stateMask=3`), the native save callback was reached. In
`analysis/live-startup-20261018-081357/events.jsonl`:

- callback target: `Ekd5.exe+0x40E240`;
- `ECX`: `0x6CEE58` (save dialog object);
- first argument: `0` (slot row);
- second argument: `0xFFFFFF9B` (`LVN_ITEMCHANGED`, -101);
- callback returned `0x6CEE58`.

The callback was entered twice, proving the list state and notification gate are
now correct. The save confirmation modal still did not appear in this bounded
run, so the remaining condition is inside the callback's subsequent business
branch, not list selection or notification delivery.
