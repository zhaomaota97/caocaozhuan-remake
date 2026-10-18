# Save dialog notification semantics

Static analysis of `FUN_00464A97` shows the custom dialog wrapper handles
`WM_NOTIFY (0x4E)` only when `hwndFrom` equals its list control handle. It
branches on notification code:

- `-0x6C`: forwards the item field through a vtable callback;
- `-0x65` (`LVN_ITEMCHANGED`): sends `LVM_GETITEMSTATE (0x102C)` for the
  reported item and invokes the dialog callback when the state is selected;
- `-8`: focus handling.

The observer now sends a notification with code `-0x65` and row index at
`NMHDR+4`, in addition to Enter/double-click/WM_COMMAND probes. The latest
run still returned `notifyResult=0` and produced no confirmation dialog, so
the remaining mismatch is the exact list notification structure/state (or the
custom wrapper instance), not an unknown save command ID.
