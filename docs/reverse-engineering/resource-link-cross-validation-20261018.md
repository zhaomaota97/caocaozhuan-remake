# Resource link cross-validation

Native resource mapping checks were rerun:

- Music mapping: `24/24`
- Sound mapping: `212/212`
- Sprite links: `2560/2560`, all within 151-entry archives
- PMAPOBJ resources: `412` resources / `206` objects; native mirrors `4/4`
- PMAPOBJ frame addresses: `80/80`
- Palette selection/conversion/controller: `5/5`
- Palette lookup: `3/3` tables, `12288` entries
- Scene sprite draw dispatch: `720/720`
- PMAPOBJ clipped framebuffer bytes: `36/36`
- Transparent blits: `15/15`

This confirms the recovered relationships among archive entries, sprite frames,
palettes, scene drawing and audio resource IDs. It does not imply every UI
event's sound role is dynamically identified.
