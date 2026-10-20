# Deferred native scenario actors

Generic scenario initialization previously dropped the native actor type.
Type-1 records had native coordinates 255/255 but could still enter movement
and action-completion collections because `nativeHidden` was unset.

On initial S_01..S_57 load (excluding the separate map31 save fixture), Web
now initializes `nativeHidden` from captured native actor type 1. Records
are retained for later script appearances, sprites/HP bars are hidden, and
existing movement/minimap/AI target filters exclude them. Automatic player
action-completion checks also exclude deferred actors. S_00 retains its
separate traced event placement handling.

S_01 browser comparison checks all six hidden records against the raw native
capture, verifies invisible sprites and absent movement actors, and still
compares every active actor's level, combat stats and movement budget. S_02
loading remains covered. Later EEX appearance events are not automatically
implemented by this fix; complete scenario progression remains open.
