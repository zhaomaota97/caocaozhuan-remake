# Battle Turn Static Chain

The recovered callers `0x4337F4` and `0x433BC8` are turn/scene transition routines, not standalone pathfinding helpers. Both update the active unit index `DAT_004B2C18`, invoke scene/text and animation helpers, call `0x438308` with the active actor's coordinate and its movement budget from `0x43F74F`, then rebuild the reachable-cost map and battle overlay through `0x4539DC`, `0x453E32`, and `0x453B13`.

`0x4337F4` decrements the active index after resolving the current scene; `0x433BC8` increments it and contains a six-iteration reverse loop for adjacent/linked actor processing. Both paths refresh the turn display and invoke `0x4350F0`/`0x451C03` to switch the active battle-side context. This is static evidence for the turn-transition state machine and explains why `0x438308` is called during turn setup even when no user click occurs.
