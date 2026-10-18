# EEX dispatch and side-effect rerun

Native dispatcher and side-effect checks were rerun:

- Dispatcher: `59/59`
- Side-effect candidate opcode checks: all listed candidates pass
- Reset table behavior: passed, including 256 table records in the reset fixture
- Configuration predicates: all listed cases pass
- Numeric predicates: `360/360`
- Effect dispatch/resource selection: `2560/2560`; missing-key commits `0`
- Unit count handler: `6144/6144`

The output confirms the handler dispatch and side-effect tables are consistent
with the recovered pseudocode and resource mappings. Full story sequencing and
AI state transitions remain outside this handler-level evidence.
