# Slot 8 Movement Cost Validation

`src/rules/movementCosts.ts` translates the four-direction cost expansion in native 0x438308 for flags=0 and restriction_mode=1. It uses native per-unit movement budgets, terrain costs, occupied-cell faction checks and stop-expansion predicates exported after loading the complete saved roster and all actor records.

All 32 maps of 640 cells match original native cost buffers exactly (20,480 cells). This verifies this search path for the current save, not all movement modes. Stop-expansion is now computed by TypeScript from current four-neighbor occupancy and the actor's category-0x21 equipment exemption. All 20,480 restriction results independently match original 0x437D59 outputs; captured masks are test evidence only, never runtime inputs. Equipment exemptions and terrain costs remain native-derived saved-state attributes. Actual movement/action submission remains unimplemented.

The suspended-process harness initializes the class table and terrain adaptation table. It replaces CRT exit-handler registration because the process has not started; search and restriction functions remain original. Earlier zero movement budgets were invalid harness results and were superseded after class initialization was corrected.
