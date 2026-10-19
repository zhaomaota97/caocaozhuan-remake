# EEX segment table format

The independent project now validates all 117 migrated `.eex` files without
using the original directory. `tools/inspect-eex.mjs` checks the `EEX\0`
magic, walks the extension records beginning at offset 6, locates the
absolute little-endian offset table after the zero-kind extension, verifies
sorted in-file offsets, and records each segment's first two words and exact
span.

Current result: **117 files and 469 segments**. A segment is marked as a
length-delimited block only when its first word is `1` and its second word
equals `segmentSize - 4`; the validator does not assign opcode semantics to
other segment bodies. This preserves the evidence boundary between binary
container recovery and the still-incomplete 108-opcode interpreter.

Run:

```powershell
node tools/inspect-eex.mjs
npx playwright test tests/eex-segments.spec.ts --reporter=line
```

The machine-readable index is `data/mappings/eex-segments-runtime.json`.
