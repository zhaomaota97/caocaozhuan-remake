# Save selection callback live proof

Changing the synthetic notification from `-101` to `-0x6C` followed the
static wrapper branch that invokes vtable `+0x3C`. In
`analysis/live-startup-20261018-081744/events.jsonl`:

- `FUN_00464E1F` was entered;
- row argument was `0`;
- current selection field `this+0x1C` was `-1` before the callback.

The callback then performs the native `0x1030` list-window update and toggles
the current-selection field. The observer's first value log treated
`this+0x18` as an inline array; static pseudocode shows it is a pointer to the
row-value table, so the displayed value is not yet decoded. This closes the
correct notification branch and leaves only row-value decoding/confirmation
business conditions.
