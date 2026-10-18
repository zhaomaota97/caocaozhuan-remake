# Save-init-gated observer rerun

The observer now tracks `save_init_ready` from the nonzero
`DAT_00496F60` observation and gates automatic `start-new` activation on that
state unless `--skip-intro` is explicitly supplied. This prevents the known
early-input ordering error in the normal path.

The bounded run `analysis/live-startup-20261018-075131` still reached the
legacy battle/save path with a zero buffer and reproduced the null write. The
trace contains an early `save-buffer-init-followup` with `0x0`, so this run is
retained as a negative control: the game instance was already in a state that
had bypassed the normal initializer before the gate could become true.

The observer change is syntax-checked and does not alter the positive normal
startup evidence where the follow-up reads a nonzero buffer.
