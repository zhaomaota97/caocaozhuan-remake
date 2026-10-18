# Effect, Animation and Sound Resource Links

`tools/export_effect_resource_links.py` joins the native effect dispatch table at executable RVA `0x866C0` with `effects.csv`, `Meff.e5`, `Mcall00..08.e5`, and the `Se_m_XX.wav` sound names encoded in each clip.

The export contains 68 effect IDs. Effects with dispatch code `255` have no resource. Codes below 100 resolve through `Meff.e5`; codes at or above 100 resolve through `Mcall(code % 100).e5`. The native selector was invoked for every Mcall code and returned the expected filename for all 9/9 cases. The complete mapping is `analysis/effect-resource-links.csv`; native evidence is `analysis/native-effect-clip-links-validation.json`.

This establishes the resource relationship: effect ID -> native dispatch code -> Meff/Mcall clip -> encoded `Se_m_XX.wav` sound. It is separate from the base attack animation-bank selector and from the critical-hit probability path.
