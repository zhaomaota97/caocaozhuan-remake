# Live EEX story probe (2026-10-18 07:19:10)

## Method

`tools/observe_live_game.py --start-new --advance-story --skip-intro --seconds 60`
was run against the isolated original runtime. The observer attached Frida hooks to
all indexed EEX handlers and recorded the native window/control tree every five
seconds.

## Observed EEX dispatch

This run entered the normal game window and produced handler events for opcodes:

`9, 20, 28, 35, 48, 50, 51`

The raw event stream is preserved at:

`analysis/live-startup-20261018-071910/events.jsonl`

This is independent evidence from the earlier new-game run; it is not treated as
full story coverage because the automated input did not advance through every
dialogue/branch.

## Native battle surface

The window remained alive for the complete 60-second interval. Repeated control
enumeration found the battle surface and these meaningful native controls:

- `ToolbarWindow32`, control id `113`
- `HexMapName`
- `HexTurnName` (two instances)
- `Weather`
- `SoldierFace`
- `Effect`, `Influence`, `MgcEffect`, `MgcInfluence`
- `ButaiSlct`, `GoButaiSlct`, `Practice`, `PracMesBox`, `TokugiEff`, `TokugiInf`

The run ended by observer timeout (`application-requested` detach), not by a game
crash. No claim is made that all controls were driven successfully.

## Boundary

This evidence expands live execution coverage but does not close the open item
`eex-full-playthrough`: only a subset of story handlers executed and no complete
victory/loss branch was reached.
