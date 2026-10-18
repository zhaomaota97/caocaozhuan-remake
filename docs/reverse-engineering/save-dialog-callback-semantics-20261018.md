# Save dialog callback semantics

Static inspection clarifies the vtable discovered in the live wrapper trace:

- `FUN_0040E240` (`vtable+0x30`) is an empty stub that returns immediately.
- `FUN_00464E1F` (`vtable+0x3C`) is the meaningful selection callback. It
  reads the selected row value from `this+0x18`, compares it with
  `this+0x1C`, sends private message `0x1030` to the list window, then toggles
  `this+0x1C` between the selected index and `0xFFFFFFFF`.

Therefore reaching `0x40E240` is not expected to open the save confirmation;
the actual state transition is driven by the wrapper's other notification
branch and `0x464E1F`. This explains why the synthetic `LVN_ITEMCHANGED`
callback can return successfully without a modal. The next dynamic probe will
target the `-0x6C` notification path and `0x464E1F` state update instead of
trying to force the empty stub.
