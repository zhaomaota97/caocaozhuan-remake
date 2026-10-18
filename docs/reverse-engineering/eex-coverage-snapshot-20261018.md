# EEX coverage snapshot

Regenerated from all 117 EEX files and 2,320 bodies, including nested
conditional bodies.

- Opcode slots: 108
- Dynamic evidence: 19
- Static handler evidence: 87
- Reserved slots: 2
- Slots present in the corpus: 92
- Slots absent from the corpus: 16

The corpus-heavy opcodes are 20 (7,613 occurrences), 52 (3,009), 9 (2,949),
79 (2,418), and 11 (2,334). The absence list is preserved in
`analysis/eex-opcode-usage.md`; absence from shipped story files is not treated
as proof that a handler is unreachable.

Reproduction:

```powershell
python tools/build_eex_coverage_matrix.py
python tools/build_eex_opcode_usage.py
```

The current matrix is an evidence index, not a claim that all static handlers
have complete runtime semantics.
