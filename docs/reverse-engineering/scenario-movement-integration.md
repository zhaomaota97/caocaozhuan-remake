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

Verification:

```powershell
npx playwright test tests/movement-costs.spec.ts tests/s01-load.spec.ts --reporter=line
npx tsc --noEmit
```
