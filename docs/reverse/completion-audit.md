# Reverse-Engineering Completion Audit

| Scope | Current evidence | Status |
|---|---|---|
| `.e5`/Ls12 and raw art formats | `extract_e5.py`, format inventory, native snapshots | verified for shipped formats |
| `.e5s` ordinary save | `save-format-readable.md`, `verify_save_objects_native.py` (`5120/5120`) | verified |
| `.e5s` battle save | `verify_battle_save_native.py` (`1160/1160`) | verified |
| `.eex` decoding/re-encoding | `eex-bodies/summary.json` (`2320` byte-exact bodies) | verified structurally |
| Runtime EEX alignment | `verify_live_eex_node_alignment.py` (`17/17` R_00 nodes) | verified for captured prefix |
| EEX side-effect native synthesis | `native-eex-side-effect-validation.json`; opcodes 7 and 106 branches | verified for isolated branches |
| Combat magnitude/hit/critical | native magnitude `652/652`, static hit/Yuxi chains | verified for covered paths |
| Movement/pathfinding | native terrain table `1590/1590`, static `0x438308` BFS chain | verified statically/native table |
| Attack/effect resources | attack banks `604/604`, scenario links `58/58`, effect clips `9/9` | verified |
| DLL inventory/resources/call graph | `dll-inventory.json`, resource map, export checks | inventory/calls verified; business semantics open |
| DLL shared-code/export boundary | `verify_dll_boundaries.py` and common `.text` hash | verified for resource DLL identity/exports |
| Full EEX story playthrough | only R_00 runtime prefix captured | open |
| Full AI and battle actions | turn transition static chain; no complete AI turn trace | open |
| `DATA.E5` entries 6–9 semantics | structure and no static loader calls | open/unresolved |
| UI save command/serializer chain | `verify_ui_save_chain.py`, `ui-save-call-chain.md`, native object round trips | verified internally |
| Unmodified UI save-then-load round trip | UI load verified separately; actual save command automation not yet successful | open |

The machine verification manifest is a regression gate for the rows marked verified; it is not a claim that the open rows are complete.
