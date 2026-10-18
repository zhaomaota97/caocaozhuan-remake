# Save slot callback live probe

The wrapper vtable remains stable at `0x486668`; its selection callback is
`Ekd5.exe+0x40E240`, with secondary callback `+0x464E1F`. A direct hook on
`0x40E240` was added for the latest run, while the wrapper still received
`LVN_ITEMCHANGED(-101)` for item 0.

No callback-enter event was emitted, so the wrapper's selected-item branch did
not invoke the vtable callback despite receiving the matching notification.
This is consistent with its subsequent `LVM_GETITEMSTATE` check failing for
the synthetic notification. The remaining work is to reproduce the exact
native list item state/mask expected by that check, rather than continue
adding notification codes.

Raw evidence:
`analysis/live-startup-20261018-081237/events.jsonl`.
