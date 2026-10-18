# Save dialog wrapper live trace

The observer now hooks `FUN_00464A97`, the recovered custom dialog wrapper.
The trace `analysis/live-startup-20261018-080926/events.jsonl` captured the
actual native notification sequence from the save list.

The wrapper's stored list HWND was `0x14121C`. Among the notifications it
received was:

- message `WM_NOTIFY (0x4E)`
- `hwndFrom = 0x14121C`
- code `-101` (`LVN_ITEMCHANGED`)
- item index `0`

This matches the static branch in `FUN_00464A97` exactly. The remaining failure
occurs inside the custom callback after the notification arrives (the observer
records an access violation while inspecting the callback path), so the
problem is no longer message selection or slot index discovery. It is the
legacy dialog object's callback/state handling for the synthetic notification.
