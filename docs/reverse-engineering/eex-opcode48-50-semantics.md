# EEX opcodes 48 and 50

These are among the most frequent script operations: opcode 48 appears 1,324
times in 59 files; opcode 50 appears 802 times in 47 files.

## Opcode 48 (`0x413010`)

Reads, in order, tags 2, 4, 4, `0x2B`, and `0x0D`. Missing values return
interpreter status 5. It then checks the native condition predicate
`0x40B922`:

- condition false: calls `0x42909D(value2, value4a, value4b, 0, value2B,
  value0D)` and returns 1;
- condition true: calls `0x4570EE(value2 & 0xFFFF)` and returns 1.

The two tag-4 values are passed as little-endian coordinate-like shorts in
the false branch; their game meaning belongs to the target function.

## Opcode 50 (`0x4132D4`)

Reads tags `0x40`, 2, 4, 4, 4 and `0x2B`, with status 5 on missing input.
It then branches on `0x40B922`:

- condition false: calls `0x429159((value2 & 0xFFFF)|0x1000, value4b,
  value4a, value2B)`, then reads scenario mode `0x418C00(&0x492F90)`;
  mode `0x32` additionally calls `0x42C858(0)` and returns 1, otherwise
  returns 2;
- condition true: resolves a target record. For mode value 1 and actor index
  below 15, status-class-2 actors use their scenario record first dword; for
  mode 0 it uses value2 directly. If no target is resolved it returns 0;
  otherwise calls `0x459487(target, low(value4b), low(value4a), value2B)` and
  returns 1.

## Native Missing-Parameter Verification

`python tools/verify_eex_opcode48_50_boundaries.py` passes 11/11 controlled
native handler calls. Each of the five opcode-48 and six opcode-50 parameter
positions is individually made unavailable. The original handlers return 5
and stop reading exactly at that position; the ordered reader-tag prefix is
compared against the expected list in every row. This includes repeated tag-4
parameters, which a tag-only failure injection cannot distinguish.

The earlier failed probe injected tags absent from a handler's parameter list,
so some cases had no missing argument and entered an uninitialized effect
path. That was a test-design error, not evidence that these early-return paths
require a full GUI interpreter. The corrected tool replaces only the parameter
reader, leaves both handlers native, and never executes their success paths.
Raw evidence: `native-eex-48-50-boundary-validation.json`.

## Native Complete-Parameter Branch Verification

`python tools/verify_eex_48_50_success_native.py` passes 18/18 cases. Opcode
48 calls either `0x42909D(18,33,34,0,3,17)` or `0x4570EE(18)` depending
on the controlled predicate. Opcode 50 calls its effect path with key 4114
and coordinates 33/34; scenario mode 50 additionally dispatches `0x42C858(0)`
and returns 1, while another mode returns 2. In the actor path, mode 0 and
65535 use ID 18 directly, mode 1 resolves controlled actor index 3 to scenario
unit ID 99, and unsupported mode 2 returns 0 without calling the actor leaf.
The native parameter read sequence is asserted in every case.

Both handlers run native code. The reader, predicate, scene getter, and effect
leaves are controlled callbacks. Native actor status and scenario-record
lookup remain active. This proves controller selection and exact argument
forwarding, not the rendering or movement performed by those leaves.
Raw evidence: `native-eex-48-50-success-validation.json`.

Both handlers' successful target effects remain incompletely validated. Their
parameter order, sentinel widths, return statuses and branch calls are taken
directly from native pseudocode; the target rendering/state functions remain
separate reverse-engineering tasks.
