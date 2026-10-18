# EEX config/reset native rerun

Additional native probes passed:

- common config opcodes: `252/252` cases;
- config predicate/reset table: passed, including all `256` reset calls;
- reset validation clears table records to the expected `0xFFFF/0` state.

These results extend verified EEX global configuration and reset semantics
without requiring live story execution.
