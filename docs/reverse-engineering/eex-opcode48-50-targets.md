# EEX opcode 48/50 target functions

Static target analysis reduces the remaining ambiguity in the high-frequency
handlers:

## `0x42909D` (opcode 48 condition-false target)

It normalizes parameter 6 to zero when above `0x12`, then calls
`0x428EB0(param1 | 0x1000, param2, param3, param4, 3, 3, 1,
param5 & 3, param6)`, returning `0xFFFF`. The operation is therefore a
parameterized effect/render command with fixed mode fields and a bounded
subtype, rather than a direct coordinate write.

## `0x429159` (opcode 50 condition-false target)

It resolves the effect key with `0x42896A`. For a live effect object whose
type from `0x418E70` is 4, it gathers object fields through `0x42AD10`,
`0x42ACF0`, `0x42ADD0` and `0x42AA20`, then calls `0x429266` to perform the
operation. On success it calls `0x42869C`; if that returns a valid value it
resets the object through `0x42AF90`, `0x42AF30`, `0x42A4B0` and `0x40E180`.
Failure to resolve an effect or complete the operation returns `0xFFFF`.

The handler's condition-true branch instead calls `0x459487`, which updates
an actor/map object at validated coordinates and optionally applies a direction
value below 4 through `0x406670`, which writes actor byte `+0x0F`. Earlier
descriptions of this argument as faction were incorrect. These targets mutate initialized runtime objects and are not
yet executed in a dedicated probe; their static argument flow is now
documented separately from the handler's parameter parsing.

Opcode 48 now has a dedicated native target probe. With a controlled active
effect entry, `0x42909D` returns `0xFFFF`, invokes `0x428EB0`, preserves the
effect key namespace and passes fixed mode fields `3,3,1`. Short arguments
are ABI-packed/sign-extended in the callback, so only the namespace, fixed
modes and return value are asserted. Raw evidence is
`native-eex-opcode48-target-validation.json`.

The opcode-50 target boundary also has a native probe. Missing effect keys
and a live entry whose type is not 4 both return `0xFFFF` without entering
the deeper object operation. Raw evidence is
`native-eex-opcode50-target-validation.json`; the successful type-4 object
path remains unexecuted because it requires initialized effect resources.
