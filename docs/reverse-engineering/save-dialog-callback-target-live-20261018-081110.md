# Save dialog callback target

The wrapper trace identified the actual callback vtable entries for the save
dialog object (`0x6CEE58`, vtable `0x486668`):

- vtable `+0x30` callback: `Ekd5.exe+0x40E240`
- vtable `+0x3C` callback: `Ekd5.exe+0x464E1F`

The `LVN_ITEMCHANGED(-101)` notification reaches the wrapper with item index
0, so the next probe hooks `0x40E240` directly to capture its arguments and
return value. This avoids guessing the callback's calling convention or
assuming that the save dialog callback is the same as the generic wrapper.

Raw wrapper evidence:
`analysis/live-startup-20261018-081110/events.jsonl`.
