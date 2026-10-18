# Save initialization order negative control

Run:

```text
python tools/observe_live_game.py --start-new --advance-story --direct-commands 101 --save-slot 0 --confirm-save --seconds 45
```

This deliberately combines automatic `start-new` with the normal intro path.
The observer clicks the new-game control before the modal startup initializer
has returned. The trace shows:

- no `save-state-init-enter` for the active game state;
- save serializer entry with slot `0xFFFFFFFF` and `DAT_00496F60 == 0`;
- the same null write at `Ekd5.exe+0x41B233` after confirming the save.

This is a negative control for ordering: normal startup alone allocates and
assigns the save buffer (see `save-buffer-assignment-live-20261018-074814.md`),
while forcing the new-game action early bypasses that initialization. It is
not treated as a file-format failure.
