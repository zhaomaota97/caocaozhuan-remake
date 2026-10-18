# EEX opcode 52 effect dispatch

Opcode 52 (`0x413567`) is a parameterized effect/object dispatch, not a
direct map write. Its handler reads value tag 2 and value tag 13. On the
native low-16-bit missing sentinel `0x8000`, it returns interpreter status 5.
Otherwise it calls:

```text
0x428B87((short)(value2 | 0x1000), (short)value13, -1)
```

The target resolves the first short through `0x42896A`, which scans a 128-
entry table at `0x49CF68`, 0x40 bytes per entry. An entry is considered live
when its flag at `0x18E50(entry)` has bit `0x8000`; its key is read by
`0x42AC90(entry)`. A missing key returns `0xFFFF` and the dispatch returns
`0xFFFFFFFF` without mutating an object.

For a live entry, `0x428B87` obtains the object with `0x426AA8(index)`,
resets it through `0x42ACB0(object, 0)`, writes parameter 2 to object offset
`+0x2C` and parameter 3 to `+0x2E` when those parameters are not `-1`, then
calls `0x428B05` to commit/refresh the effect table. The handler always
returns interpreter status 1 after invoking this target.

This explains the `0x1000` bit observed in the dynamic handler probe: it is
part of the effect key namespace. The probe verified the missing-input and
target-call boundaries; it did not execute a live initialized effect table,
so object lookup, mutation and presentation timing remain static-only.
