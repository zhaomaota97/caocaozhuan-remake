# Unit animation source colors across battlefield palettes

Every original indexed pixel in all Unit_atk, Unit_mov and Unit_spc entries
was counted, then each used nonzero index was compared across all 58 Spalet
records after high-nibble conversion. Each family has exactly one visible
color profile, no missing used entries and no affected source resources.

| Bank | Entries | Source Pixels |
| --- | ---: | ---: |
| Unit_atk | 151 | 7,421,952 |
| Unit_mov | 151 | 3,826,944 |
| Unit_spc | 151 | 1,739,520 |

All 12,988,416 source pixels can therefore use the existing exported map31
source-color conversion across battlefield palettes. The historical path
name does not limit their source colors to map31. This supersedes the earlier
unverified scene-color concern for these three raw banks specifically.

It does not prove final displayed actor pixels: acted-state darkening,
status colors, flashing, indexed compositing, side-dependent selection,
frame selection and animation timing require their own native rules. Nor
does an exhaustive resource comparison replace a live battle screenshot.

Machine-readable counts and per-scene hashes: `unit-scene-colors.json`.
Reproduce: `python tools/audit_unit_scene_colors.py` in reverse workspace.
