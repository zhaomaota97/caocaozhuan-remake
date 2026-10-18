# Movement Evidence Correction

The native neighbor table at 0x48DF68 contains eight entries. This alone does not establish eight-direction movement. The expansion loop in 0x438308 uses indices 0 through 3 only: north, east, south and west.

Slot 8 now stores each actor's native movement budget (0x43F74F) and all 30 terrain costs (0x43F7CF). Costs use the low byte of the native return value; 255 means impassable. These values were calculated after loading the saved roster, actor records, item table and terrain adaptation table.

The old uniform-cost eight-direction highlight is disconnected from the scene. Movement submission remains disabled until the occupancy and restriction predicates are reproduced. Selecting a unit only highlights its current cell.
