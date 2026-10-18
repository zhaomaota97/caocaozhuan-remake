# Save slot notification probe

The slot activator now sends four native activation forms after selecting row
0: Enter, `NM_DBLCLK` through `WM_NOTIFY`, a direct list-view double-click, and
`WM_COMMAND` with the list control's double-click notification.

In `analysis/live-startup-20261018-080533/events.jsonl`, all posts were
accepted (`queued: [1,1,1]`), but the parent dialog returned `notifyResult=0`
and `commandResult=0`; no `保存` confirmation modal appeared. The list row
selection itself returned `selection=1`.

This narrows the remaining UI save issue to the original dialog's private
activation handler or its required hit-test state. It does not change the
already verified initialized serializer and raw file-path boundaries.
