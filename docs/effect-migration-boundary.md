# Effect Migration Boundary

The remake currently carries the reverse-engineered effect tables and assets:

- `data/mappings/effects.csv`
- `data/mappings/effect-resource-links.csv`
- `data/mappings/mcall-timeline.csv`
- `public/assets/effects/Mcall00.gif` through `Mcall08.gif`

The native evidence establishes effect ID -> dispatch code -> `Meff`/`Mcall` resource -> `Se_m_XX.wav`, plus cost, terrain, status-writeback, and pixel-blend rules. The battle scene has not yet wired every effect ID into a complete strategy/item inventory and target-specific result controller. Until that integration is validated against the native controller, strategy and item actions remain target-selection/state-flow only; no invented damage, healing, status, or resource consumption is used.

The same verified fields are now consolidated in `data/mappings/effects-runtime.json` (73 effect records) for the future controller; it is a provenance index, not an implementation of unverified effect semantics.
