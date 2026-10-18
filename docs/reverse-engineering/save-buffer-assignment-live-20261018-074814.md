# Save buffer assignment live proof

The observer now hooks the first known post-allocation call
`FUN_0047FD13`. In the normal startup trace:

1. `FUN_0041BF67` enters.
2. `FUN_0047FA40(..., size=4796304)` returns `0xAB6740`.
3. `FUN_0047FD13` immediately reads `DAT_00496F60 == 0xAB6740`.

Raw evidence:
`analysis/live-startup-20261018-074814/events.jsonl`.

This is direct dynamic proof that the normal initializer assigns the allocated
save buffer to the global pointer. It closes the initialization side of the
save serializer chain. The null pointer observed in the automated battle-save
probe is therefore conclusively a path-order/setup issue, not an allocator or
save-format defect.
