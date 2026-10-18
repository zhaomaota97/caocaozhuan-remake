# EEX opcode 20 dialogue handler

Correction: the native reader now passes 8 strict, unmodified-code tests in
`eex-native-cursor-validation.md`. The earlier synthetic probe did not show
that dispatcher setup was required; its assertion and pointer inspection
were incorrect. In particular, field `+8` counts scalar-reader bytes but
does not count string payload bytes, so value 498 is not a file offset.

Opcode 20 maps to native handler `0x413661` and is the most frequent
non-terminator opcode in the decoded corpus (3,328 occurrences across 59
script files). The static handler accepts the interpreter object, obtains a
script cursor through `0x4183F7(this, 5)`, and returns 5 immediately when the
slot-5 cursor is unavailable.

## Native path

The handler reads a dialogue line from the cursor. A line beginning with
`&` selects a speaker/portrait form: the following two bytes can be a numeric
unit ID or a text lookup, and the selected unit must have native class/state
kind 2. Otherwise the line is copied as a CP936/DBCS string into a 0x400-byte
local buffer. The handler resolves text labels with `0x41EEC0` when needed,
then calls `0x4179A5` to copy the line while stopping at the next `\n&`
boundary.

If the native condition predicate `0x40B922` is false, it uses the standard
text path `0x42D5F1(buffer, speaker, 0x20)`. When the predicate is true and
the speaker ID is valid, it calls `0x45965D(buffer, speaker)` for the
speaker-aware presentation. It scans to the next `&` line and repeats; the
handler returns 1 after the final line. Missing slot-5 cursor returns 5.

## Runtime evidence

The bounded GUI trace in
`analysis/live-startup-20261017-194421/events.jsonl` captured 26 EEX
dispatches and 17 handler entries, including opcode 20. The real interpreter
object is `0x492F90`, script buffer `0x3BE04A0`, and state slot table
`0x3BF1E40`. The live opcode-20 entry recorded cursor `0x3BE06B9` and
cursor field value `498`. The script buffer begins with the native header:

```text
45 45 58 00 01 02 00 00 00 00 0e 00 00 00 01 00
```

The exact pre-dispatch cursor is null in the first interpreter snapshot,
because the dispatcher has not yet selected a slot; the handler entry has a
valid cursor. This distinguishes the interpreter object's stable state
pointer from the per-dispatch cursor and explains why a standalone object
constructed without dispatcher initialization entered the `0x80000000`
failure branch.

## Native Parsing Verification

`python tools/verify_eex_dialogue_native.py` passes 11/11 cases with actual
CP936 tagged-string inputs. Native opcode 20, parameter reader, line copier,
numeric conversion, actor status getter and unit-ID lookup all execute.
Only the condition predicate and final plain/portrait display leaves are
controlled. No parameter reader is replaced.

Verified cases include plain narration in both predicate modes; `&03` selecting
actor slot 3 whose unit ID is 99; a second `&04` section selecting unit 100;
status-class-1 slot 5 returning 1 without displaying; and wrong tag 2 returning
5 without displaying. Every display's exact CP936 bytes, speaker ID and plain
style 0x20 are checked. String pointer advancement includes the null byte,
while counter +8 increases by only the two-byte argument tag.

The numeric speaker check is actor **status class** at record+0x0C, not the
unit's combat class/兵种. Raw evidence: `native-eex-dialogue-validation.json`.

## Limits

Additional cases execute native name resolution `0x41EEC0` and current-unit
lookup `0x45602B`. Controlled unit record 99 stores CP936 name bytes at
`unit+8`; named dialogue selects it in both story/plain and battle/portrait
modes. An unknown name yields speaker 65535 and plain text. `&` followed
immediately by newline uses the current unit only when an actor record has
status 2 and positive HP; zero HP falls back to speaker 65535. The current
unit object at `0x4B5DF0` is seeded with ID 99; no name/actor lookup function
is replaced. These inputs establish selection rules without claiming the
controlled roster matches every real scenario.

The runtime trace did not capture a complete multi-line dialogue presentation
with both speaker and non-speaker branches, so the text/UI leaf timing is not
claimed dynamically. The static pseudocode and live object/cursor addresses
are independently evidenced. A future deeper story trace should capture the
cursor bytes now instrumented by `observe_live_game.py` and validate the
speaker branch without replacing presentation functions.
