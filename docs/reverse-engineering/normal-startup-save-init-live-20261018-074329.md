# Normal startup save initialization

Run:

```text
python tools/observe_live_game.py --seconds 20
```

Unlike the forced new-game path, this run entered `FUN_0041BF67` and emitted
`save-state-init-enter` before the bounded observer ended. The event stream
also shows DATA.E5 entries `0`, `1`, `3`, and subsequent initialization reads
while the normal startup UI was active.

No `save-state-init-return` was observed within the bound because the native
initializer owns a modal startup/dialog loop. This is positive evidence that
the normal executable path does initialize the save buffer; the null buffer in
the automated save test is caused by entering the battle UI through a path that
did not complete this initializer.

Raw evidence:
`analysis/live-startup-20261018-074329/events.jsonl`.
