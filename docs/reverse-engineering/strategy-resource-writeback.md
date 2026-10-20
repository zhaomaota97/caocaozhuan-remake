# Strategy resource writeback

Native `0x422F0D` was rerun: all 12 controlled resource cases passed.
`src/rules/strategyResourceWriteback.ts` independently matches their HP/MP
outputs. The native probe suppresses rendering, experience, equipment
progression and refresh callbacks, leaving resource arithmetic and native
HP/MP setters active. It never resumes the native main thread.

The action success dword at `+0x4AC` gates all writes. Cost is effect runtime
byte `+0x0E`; equipment category 49 supplies an integer divisor when present.
MP subtracts the truncated cost with a zero floor. Effect 20 restores the
actor's HP by the action magnitude, limited to missing HP. Effect 22 restores
MP after cost subtraction, limited to missing MP. Final native setters cap
HP/MP at their maxima. The cost calculation itself is not an affordability
check; eligibility must run earlier in the complete controller.

The twelve native cases cover costs 0/13, insufficient/exact MP, over-max MP,
divisors 2/3/20, and both restoration branches. The success-zero Web test
has static native evidence; it was not included in that original matrix.
Zero divisors are rejected explicitly; invalid/overflowing inputs are outside
this port's claim. This helper is not yet called by incomplete Web effect
previews because target eligibility and actual result controllers remain open.

Reproduce: `python tools/verify_effect_cost_native.py` in the reverse
workspace. Evidence: `native-effect-cost-validation.json`.
