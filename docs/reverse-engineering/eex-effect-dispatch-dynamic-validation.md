# EEX opcode 52 effect-table dynamic validation

## Strengthened Verification

The latest extension passes 2,560/2,560 cases: all 128 table positions,
parameter-2 inputs -1/0/1/18 and parameter-3 inputs -1/0/3/32767/-32768.
Original resource resolution `0x426871` and object binder `0x42A4B0` now
execute as well as lookup/reset/setters. Valid parameter 2 writes its index
at object+0x2C, binds the pointer `0x48B920 + index*9` at +0x34, and widens
the definition's second byte into +0x2A. Both pointer RVA and type byte are
checked against the original executable's PE bytes independently of the
native getter. For -1 all three seeded fields remain unchanged.

The JSON preserves the 19 nine-byte definitions read from the executable.
Only indices 0/1/18 are exercised here, not all possible resource indices.
Graphics submission remains a recorded callback; this proves binding and
field updates, not final pixels or sound. Historical coverage below describes
earlier probe revisions, superseded by this larger matrix.

The current tool passes 640/640 cases: all 128 table positions times third
arguments -1/0/3/32767/-32768. Every record starts with nonzero reset field
0x6A6A and parameter fields 0x2345/0x3456. The matched record's reset changes
to zero; all unmatched reset/third fields remain unchanged. Where possible
the preceding record has the same key but lacks the active bit, establishing
that native lookup skips it.

Parameter 2 stays -1 and therefore retains 0x2345 without entering resource
lookup. Parameter 3 either retains 0x3456 for -1 or writes the exact 16-bit
input to +0x2E. Each successful call invokes the recorded commit once;
missing key invokes it zero times. The commit function alone is replaced;
native lookup, reset and field setters execute unmodified.

This supersedes the original three-row test below, whose zero-initialized
reset field could not prove a reset actually occurred. No rendering/resource
selection equivalence is claimed by either test.

`python tools/verify_eex_effect_dispatch_native.py` executes the original
`0x428B87` with `0x428B05` replaced by a no-op commit callback. Three entries
(indices 0, 1 and 127) are initialized in the native table at `0x49CF68`:

- entry size `0x40` bytes;
- active flag `+0x28 = 0x8000`;
- key `+0x3A = 0x1234 + index`.

For each key, native lookup succeeds, returns 0, preserves the active flag
and resets object field `+0x1A` to zero. A missing key returns `0xFFFFFFFF`.
Parameters 2 and 3 are both `-1`, so the probe intentionally skips native
resource-pointer lookup and only validates key lookup, bounds (including
index 127), reset and return behavior. The commit/refresh leaf is replaced
only to avoid graphics state; object fields written by the skipped parameter
branches remain outside this test.

Raw result: `native-eex-effect-dispatch-validation.json`.
