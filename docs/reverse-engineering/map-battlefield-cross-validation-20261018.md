# Map and battlefield cross-validation

Map, terrain and saved battlefield exports/checks were rerun:

- Terrain grids validated: `58`
- PMAP arrays validated: `74`
- Saved maps rebuilt: `10`
- Active terrain overlays: `113`
- Gate overlays: `14`
- Native minimap rectangles: `32/32`
- Native map readers: `784646/784646` across `132` maps
- Native terrain masks: `74/74`
- Native movement checks: `1590/1590`

The actor-grid exporter requires a captured `actors.bin`; no such artifact was
present in the current saved-battlefield export, so that optional export was not
counted as a pass.
