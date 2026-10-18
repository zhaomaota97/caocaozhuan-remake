# Reverse Runtime Integration

This document maps verified reverse-engineering artifacts to the browser runtime.

| Verified source | Runtime integration |
|---|---|
| `battle-map-31.json`, `battle-save-actors.csv` | Map 31 terrain, dimensions, actor positions and unit records |
| `native-idle-frame-validation.json` | Direction/status/phase idle frame selection |
| `native-movement-table-validation.json`, `movement-sounds.json` | Movement cost, path frames and terrain sound selection |
| `native-sound-mapping-validation.json` | Native sound bank preload and filename resolution |
| `effects-runtime.json`, `effect-resource-links.csv` | Strategy submenu, effect metadata, `Mcall` visuals and `Se_m` playback |
| `native-combat-magnitude-validation.json`, ordinary combat validators | Ordinary attack, accuracy, critical/Yuxi, RNG and writeback rules |
| `native-target-shape-matrix.json` and `target-shapes.json` | Attack/target candidate geometry; generic shape-0 strategy preview |
| `native-ui-templates.json`, toolbar mappings | Fixed-pixel action menu, toolbar icons, modal geometry |

The browser does not invent strategy/item damage or status outcomes where the
native result controller is not fully recovered. Those paths expose verified
resource metadata and target selection while retaining the remaining boundary.
