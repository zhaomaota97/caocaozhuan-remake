# Unified EEX coverage summary

The new `tools/build_eex_coverage_summary.py` combines the static matrix, all
bounded live runs, native probe artifacts, and the unobserved priority list.

- Static slots: `108` total, `21` dynamic artifacts, `85` static-only, `2`
  reserved.
- Live union: `15` opcodes across `17` runs.
- Native probe artifact families: `8`.
- Unobserved priority candidates: `91`.

Machine output: `analysis/eex-coverage-summary.json`. The summary explicitly
keeps `completionClaim=false`.
