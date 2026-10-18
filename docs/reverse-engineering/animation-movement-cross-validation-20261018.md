# Animation and movement cross-validation

Native movement/animation checks were rerun:

- Idle frames: `640/640`
- Idle frame selector: `512/512`
- Direction/mirroring movement checks: `1590/1590`
- Movement-budget branches: `2544/2544`
- Equipment movement budgets: `487/487`
- Frame clock: `280/280`
- Movement sounds: `960/960`

Together with the existing 636 animation samples and 933 movement-path samples,
these checks cover idle selection, facing/mirroring, timing, movement budgets
and terrain/audio dispatch without inventing an alternate animation model.
