# Equipment experience and level writeback

Reproduce with `python tools/verify_equipment_experience.py`.
Latest native result: 18,900/18,900 cases matched level, experience byte,
upgrade-notification count and RNG state. Raw rows and per-item caps are in
`native-equipment-experience.json`.

## Native rule

Function `0x4082D6(unit, slot, gain)` only updates slots 0 and 1. Slot 2
and empty item ID 255 are unchanged. The three bytes per equipment slot
are item ID (`unit+0x2E+slot*3`), level (`+0x2F+slot*3`) and experience
(`+0x30+slot*3`).

For an equipped item, compute `total = storedExperience + gain`. While
`total >= 100` and level is below its cap, increase level by one, dispatch
one level notification, then subtract 100. If the final level is below
the cap, store the remaining total as a byte. Otherwise store experience
255. Reaching the cap discards surplus experience.

The cap is 9 when the item's category byte is below 18 and odd; otherwise
it is 3. This classification was checked independently against Data.e5
for all 104 item definitions, as well as querying native `0x40C76E`.
These results describe the updater's behavior, including deliberately
unusual test equipment; they do not establish which items the normal
equipment UI allows in each slot.

The test matrix covers all 104 definitions plus empty ID 255, slots 0/1/2,
levels 0/2/3/8/9, stored XP 0/99/255 and gains 0/1/100/255. Invalid or
over-cap initial levels are deliberately included to document byte-level
behavior. No RNG state change occurred in this updater with its notification
leaf replaced.

## Calling-convention correction

Ghidra declares `0x4083EF` as fastcall with four parameters, including
`extraout_ECX/EDX` artifacts. The native caller at `0x40839A..0x4083AC`
instead pushes slot, pushes unit ID, calls the function and adds 8 to ESP.
The probe therefore replaces it with a **cdecl two-argument** callback.
Treating Ghidra's inferred prototype as authoritative corrupted the test's
stack at the first upgrade. The corrected callback records notifications
without performing UI/resource loading.

## Remaining scope

This verifies equipment XP writeback, not the amount awarded by each
attack, unit XP/level growth, equipment attribute changes after upgrading,
notification rendering or random behavior inside the replaced notification.
Native attacker reward `0x405C6C` grants unit XP through `0x408950` and
weapon XP through this updater; defender writeback grants armor XP through
the same updater. Their award calculations remain separate requirements.
