# ITEM source colors are shared by all battle palettes

Every nonzero pixel index in all 104 ITEM images was compared across all
58 original Spalet records. Every used index fits inside every record, so
no missing-tail assumptions enter this comparison. After the native
high-nibble conversion there is exactly one visible source-color profile:
zero palettes differ from map31, and zero items have changed source pixels.

This establishes that the existing 104 `items-map31` PNGs can serve as shared
ITEM source images for all 58 battlefield palettes despite their historical
directory name. Creating 58 duplicate image banks would add no source-color
fidelity. It does not establish scene-independent animation results: native
blending reads scene background colors and builds a scene-specific lookup.
Those must retain their actual scene palette and runtime transition state.

Machine-readable results in `item-scene-colors.json` include each palette's
visible-color hash, changed indexes and affected item list (all empty).
Reproduce: `python tools/audit_item_scene_colors.py` in reverse workspace.
This is an exhaustive original-resource comparison, not a dynamic native
animation capture.
