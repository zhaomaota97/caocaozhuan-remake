# Native sound ID usage rerun

The new `tools/summarize_sound_id_usage.py` groups the 128 possible native
sound-selector IDs by recovered call site, preserving dynamic expressions and
mode values. It found 31 constant IDs plus 3 dynamic call sites.

Most calls use mode `1`; IDs `15`, `16`, and `18/19` also occur with mode `0`.
The most frequently referenced constants are ID `8` (15 call sites), ID `2`
(10), ID `1` (9), and ID `0` (8). This is a call-site map, not a guessed
semantic name map: the original wrapper selects entries from `SE00.WAV` or
`SE_E_01.WAV`, and only the live sound hooks can establish the actual playback
context for a given path and flags.

Machine-readable output: `analysis/native-sound-id-usage.json`.
