# Battle movement probe after live surface detection

Trace: `analysis/live-startup-20261018-103724`

The observer now schedules the movement probe inside the `battle-surface-detected` branch. After slot 8 load exposed the battle window and `HexMapName`, it clicked screen coordinates `(898,546)` and `(946,546)` in sequence and recorded `move-test-after-battle-surface`. The process detached normally without the COMCTL32 save-test crash. A native actor snapshot was not requested because the native battle-ready hook was not reached in this path; this is a timing result, not a failed movement probe.
