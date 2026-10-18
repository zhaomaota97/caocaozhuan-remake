# Native UI Sound Call Index

`tools/index_native_ui_sound_calls.py` scans recovered pseudocode for calls to wrapper `0x47467A`, which dispatches `SE_E_XX.WAV`/related sound files through `sndPlaySoundA`. It found 114 static call sites and 31 constant sound IDs. The JSON preserves caller addresses, source lines, expressions, and modes.

This is provenance evidence only. A constant ID is not labeled “select” or “cancel” unless the caller's UI event path or a runtime sound trace establishes that relationship.
