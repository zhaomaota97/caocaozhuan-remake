# Native EEX Cursor Reader

Run `python tools/verify_eex_cursor_slot5_native.py`. All 8 cases execute
native `0x4183F7` and its underlying readers without replacing any function.
The original weak assertion `returned >= 0` was removed: it accepted every
unsigned return value and could not establish a match.

The corrected probe asserts returned scalar/string bytes, actual pointer
advance, and the interpreter counter at `+8` independently.

| Requested tag | Matched input | Pointer advance | Counter increment |
| --- | --- | --- | --- |
| 1 | Any raw opcode word | 2 | 2 |
| 2 | Tag 2 and a word | 4 | 4 |
| 4 | Tag 4 and a dword | 6 | 6 |
| 5 | Tag 5 and zero-terminated bytes | 2 + string length + 1 | 2 |

Tag-2 mismatch returns `0x8000`; tag-4/5 mismatch returns `0x80000000`.
All mismatches consume only the two-byte input tag. Both empty strings and
CP936 byte strings pass. The string result is the original string pointer,
not a newly allocated string.

Crucially, pointer `object+0x0C` and counter `object+0x08` are not redundant.
The native zero-terminated string reader `0x40FD4A` advances the pointer
directly, without using byte reader `0x40FCB1` that increments the counter.
Thus the live opcode-20 counter value 498 cannot be treated as the byte
offset from the EEX file base. This explains pointer/counter divergence
without requiring a missing interpreter mode or extra dispatcher setup.

The earlier synthetic string probe already reached the successful tag-5
branch but read `text.readPointer()` instead of `object+0x0C` and had no
meaningful assertions. Its earlier failure interpretation is withdrawn.

This proves the tested well-formed reader paths. It does not prove buffer
bounds, malformed strings without a terminator, complete dialogue rendering
or all other argument-tag semantics.
