# Short palette records retain prior state

Native wrapper `0x41E050` overwrites only the decoded resource byte count,
then shifts all 768 current palette bytes right by four. It does not clear
the destination beforehand. A controlled read of Spalet entry 31's actual
738 bytes with prior buffer values 0/15/128/255 produces four matching native
captures. The final 30 bytes are the prior bytes shifted right by four.
Web `nativePaletteLoad` matches every output. File operations, resource read,
UI and lookup generation are replaced; the conversion loop remains original.

This disproves treating zero padding as a universal loader rule. The actual
preceding runtime palette still needs live tracing. Converted item art and
the item blend fixture using zero padding are valid only for that explicit
initial-tail assumption. They do not prove universal campaign colors for
indexes 246..255. Existing frame rules must preserve full palette state
when the native scene loader is ported.

Reproduce: `python tools/verify_short_palette_tail_native.py` in reverse
workspace. Evidence: `native-short-palette-tail.json`.
