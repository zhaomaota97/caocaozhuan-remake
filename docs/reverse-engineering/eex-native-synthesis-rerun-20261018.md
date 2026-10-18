# EEX native synthesis rerun

The independent native probes completed four additional handler families:

- enemy setup: `24/24` contexts, `480` records;
- restore units: `288/288` contexts;
- amount updates: `96/96`;
- animation commands: `970/970`.

Machine outputs:

- `analysis/native-eex-enemy-setup-validation.json`
- `analysis/native-eex-restore-units-validation.json`
- `analysis/native-eex-amount-validation.json`
- `analysis/native-eex-animation-command-validation.json`

These validations expand native branch coverage without claiming that every
corresponding story opcode has been observed in a live GUI playthrough.
