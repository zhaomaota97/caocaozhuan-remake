# Remaining Reverse-Engineering Work

Current EEX evidence snapshot: 15 opcode slots observed across 18 live runs;
native synthesis adds independent branch coverage for enemy setup, unit
restore, amount, animation, config/reset, dialogue/timer, and effect/target
families. These measurements do not replace full story execution.

The verification manifest currently passes 57/57 evidence groups. The following items remain explicitly open because their required evidence is not yet complete:

1. Execute and trace all 108 EEX opcodes through complete story playthroughs; current runtime proof covers 28 opcode slots (including the R_00 prefix and live new-game handlers), while 78 remain static-only.
2. Recover business semantics for every exported DLL function; resource tables and call edges are complete, but semantic labels are not.
3. Capture a successful UI-driven battle action through `0x438308`, then correlate the movement cost map and actor coordinate changes before/after the action.
4. Trace AI turn selection and attack execution over a complete battle turn.
5. Resolve semantic roles for `DATA.E5` entries 6-9; their structure is known, but no loader/request path has been observed.
6. Add an unmodified UI save-then-load round-trip test; native serializers and UI loading are separately validated.
7. Complete dynamic target-list validation for all actor contexts; actor offset 0 shapes 8-15 (`85/85`) and actor offset 2 shapes 0-15 (`128/128`) are validated, with additional offset 3/4/5/7 context evidence. Remaining failures are context-dependent higher-shape initialization boundaries.
8. Wire the verified effect/resource/timeline tables into complete strategy and item result controllers; current remake support is target selection and state flow only.
9. Correlate the 114 static `0x47467A` sound-wrapper callers with UI events to identify selected/cancelled menu sounds; current evidence only proves the wrapper and constant IDs.

These are scope boundaries, not claims that the corresponding systems are absent.

## Aggregation note

The machine-readable `open-work-items.json` intentionally aggregates these
fine-grained rows into seven top-level gaps: rows 1 and the EEX subparts are
covered by `eex-full-playthrough`; rows 3, 6, and 9 are covered by the UI
input/save-load boundary; and rows 4 and 8 are covered by the AI/battle-state
boundary. The human list is therefore more detailed than the machine count,
not inconsistent with it.
