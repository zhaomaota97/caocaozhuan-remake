# EEX low-frequency native rerun

Independent native synthesis passed the low-frequency and conditional handler
probes:

- low-frequency cases: opcodes `10,3,12,13,30,7` all passed;
- conditional cases: opcodes `14,73,84` passed for both false and true
  conditions, including expected nested calls.

Machine outputs:
`analysis/native-eex-low-frequency-validation.json` and
`analysis/native-eex-conditional-validation.json`.

These are isolated native branch validations, not live story-playthrough
coverage, but they expand verified semantics for handlers not seen in the
runtime opcode union.
