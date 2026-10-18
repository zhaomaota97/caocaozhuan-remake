# Live EEX alignment rerun

The latest automatic new-game trace was checked against the on-disk script:

- Runtime prefix/header alignment: `4/4`
- `R_00.eex` 128-byte prefix match: pass
- Live handler argument/opcode matches: `25/25`
- Unique live handler opcodes: `15`
- Dispatch node alignment: `17/17`
- Dispatcher calls observed: `26` (returns observed: `25`)

One initial non-script dispatch node is a header/control record and is retained
as such; the 17 script nodes align to the decoded EEX node offsets. This is
direct runtime-to-disk alignment evidence, not a claim of full story coverage.
