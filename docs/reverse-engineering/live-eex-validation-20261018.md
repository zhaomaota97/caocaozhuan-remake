# Live EEX Validation Refresh

Re-running the strongest captured startup trace (`live-startup-20261017-040510`) confirms:

- 17/17 dispatcher handler events match their opcode argument.
- 17/17 parsed dispatch nodes match the corresponding `R_00.eex` node offsets.
- The runtime buffer matches the `R_00.eex` first 128 bytes.
- Observed opcodes include 9, 20, 28, 35, 48, 50, and 51.

The first two startup cursor records remain header/setup records without an opcode node; they are retained as part of the 17-node alignment result rather than discarded.
