# EEX handler semantics rerun

The handler semantics exporter was regenerated from the opcode index and
recovered pseudocode:

- Opcode rows: `108`
- Handler pseudocode bodies present: `106`
- Each row records handler address, parameter-reader tags, called functions,
  referenced globals and suspected global writes.
- Reserved/terminal slots remain explicitly represented.

The machine-readable source is `analysis/eex-handler-semantics.json`.
This is a static semantic index; dynamic evidence is tracked separately in the
EEX coverage matrix and live validation artifacts.
