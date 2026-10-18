# Background battle probe

Trace: `analysis/live-startup-20261018-104125`

The observer ran with `--background`, kept Ekd5 hidden, loaded slot 8, detected the battle surface, and sent the movement probe through `PostMessageW` without foreground activation. The two clicks were recorded at `(898,546)` and `(946,546)`. The post-move snapshot RPC was reached but rejected the state because the global map dimensions were not initialized at that boundary; this is recorded as a state-timing diagnostic rather than a crash. The observer detached normally.
