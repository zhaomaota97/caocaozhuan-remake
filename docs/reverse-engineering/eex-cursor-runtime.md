# EEX primitive cursor in the Web port

`src/rules/eexCursor.ts` ports the bounds-checked readers used by the native
EEX analysis tools: little-endian 1/2/4-byte integers, zero-terminated byte
strings, and tagged parameters. A mismatched tag returns the same native
sentinels (`0x8000` for short values and `0x80000000` for long/string
values); matching tag 5 returns raw bytes for later code-page decoding.

The cursor rejects invalid spans, truncated integers and unterminated strings.
It does not assign opcode meaning or decode GBK text. Two browser tests cover
advancement, byte order, mismatch sentinels and truncation boundaries.
