# Native UI sound caller roles

Generated from `native-ui-sound-calls.json` by static call-site classification.

| Role | Calls | Evidence scope |
|---|---:|---|
| effect-or-battle | 2 | Known effect/battle call sites |
| movement-animation | 11 | Movement animation routine |
| target-selection | 4 | Target selection routine |
| turn-transition | 6 | Player/AI phase transition routines |
| unclassified | 91 | No sufficiently specific role evidence |

This report classifies context only. It does not assign select/cancel sound IDs;
those require a dynamic UI trace that reaches the corresponding native handlers.
