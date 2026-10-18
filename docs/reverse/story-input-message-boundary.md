# Story Input Message Boundary

The startup trace `analysis/live-startup-20261017-040811/events.jsonl` shows that story initialization sends custom messages `641` and `642` through `SendMessageW` to the main game window and the `SmallMap` window. Typical combinations are:

| message | target | wParam | lParam |
|---:|---|---:|---|
| 641 | main window / SmallMap | 0 or 1 | `0xC000000F` |
| 642 | main window / SmallMap | 1 or 2 | `0` |

The trace contains no `list-input` events while the R_00 story interpreter runs. This establishes that the ordinary list-control input hook is not the story progression boundary; input is handled in the custom window-message layer. The automatic story mode in `observe_live_game.py` is retained, but Enter/Space injection is not treated as successful progression until a subsequent EEX interpreter call or a message-state transition is observed.
# Timeline verification

`tools/summarize_story_message_timeline.py` counts and orders custom messages. In trace `analysis/live-startup-20261017-040811`, there are 17 message-641 events and 13 message-642 events, followed by one interpreter call and 26 dispatcher calls. No second interpreter call occurs after the message bursts, so these messages are recorded as startup/render synchronization in this run, not proof of story advancement.
