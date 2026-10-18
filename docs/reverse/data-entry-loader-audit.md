# `DATA.E5` Entry Loader Audit

The native loader `0x41B51E` is called by six dedicated initializers:

| Entry | Initializer | Record count | Native record size | Destination table |
|---:|---:|---:|---:|---|
| 0 | `0x41B666` | 512 | `0x48` | unit/character table at `0x4A1B68` |
| 1 | `0x41B6CF` | 104 | `0x19` | item/effect table at `0x4A1140` |
| 2 | `0x41B7EF` | 58 | `0x28` | secondary character table at `0x4AEB68` |
| 3 | `0x41B72F` | 53 | `0x1B` | terrain/class table at `0x4ABFA0` |
| 4 | `0x41B78F` | 27 | `0x3C` | growth/effect table at `0x4AE4E0` |
| 5 | `0x41B84F` | 68 | `0x46` | effect/status table at `0x4AF4C0` |

Each initializer first calls `0x41B51E(DATA.E5, entry, destination)` and only deserializes records when that call succeeds. Entries 6–9 have been decoded structurally (`analysis/data-entries-6-9.md`) but no corresponding static initializer or live startup request has been found; their sparse repeated rows (`D6 D5 B6 CB` plus zero padding) are therefore recorded as unresolved/unused rather than assigned speculative semantics.

`tools/audit_data_loader_calls.py` scans every recovered pseudocode file. Excluding the loader's own formal parameter declaration, all literal entry arguments are exactly `{0,1,2,3,4,5}`; there are no static calls with entry 6, 7, 8, or 9. The machine-readable call inventory is `analysis/data-loader-calls.json`.
