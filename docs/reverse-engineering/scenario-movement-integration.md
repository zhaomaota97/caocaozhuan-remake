# Scenario movement integration corrections

Movement restriction and occupancy code previously extracted the battle slot
using `Number(id.slice(5))`. This worked for saved IDs such as `unit-0`, but
returned NaN for scenario IDs such as `s00-slot-0`. Both factions then mapped
to the same Boolean group, so enemy occupancy and hostile adjacency could
be treated as friendly.

Slot extraction now explicitly recognizes the saved and scenario ID forms.
The native slot boundary at 35 remains unchanged. The test reruns all 32
original saved-actor movement and adjacency fixtures with scenario-form IDs,
and compares against the same captured native restriction and cost maps.
This proves naming independence for those fixtures, not complete native
movement traces for every campaign scenario.

Scenario movement state now comes from runtime actor byte `+0x1D`, exported
from each raw actor capture. Previously it was hardcoded to 1, causing native
`0x43F74F`'s low-state movement penalty even for actors with neutral state 3.
The browser S_01 test checks the state supplied to every living movement
actor against the raw native capture. Later state-controller writeback is
still separate work.

The capture harness now also invokes native `0x43F74F` directly for every
record. All 2,436 captured actors across the 58 scenario expansions match
the Web movement-budget calculation using class, equipment, runtime state
byte `+0x1D`, and status byte `+0x1E`. Raw results are `nativeMove` in
`data/scenarios/native-units/S_00..S_57.json`. This includes hidden records
in controlled initialization, not a full campaign movement playthrough.

Live scenario movement actors now expose the calculated budget instead of
the previous fixed value of 6. S_01 browser coverage checks both tier and
calculated budget against each living actor's native capture. The unit
information dialog also reads current combat attributes rather than looking
only in the slot-08 save snapshot.

Verification:

```powershell
npx playwright test tests/movement-costs.spec.ts tests/s01-load.spec.ts --reporter=line
npx tsc --noEmit
```
