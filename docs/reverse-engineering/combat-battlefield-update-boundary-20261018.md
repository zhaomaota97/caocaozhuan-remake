# Combat battlefield update boundary

Static inspection shows the previously suspected `FUN_004539DC`/
`FUN_00453B13` pair is renderer/view state, not actor HP persistence:

- `FUN_004539DC` writes a byte at `this+0x1B85`, stores a four-byte cursor/
  coordinate value at `+0x1B86`, clears a `0x640`-byte view buffer via
  `FUN_0047FD13`, then calls `FUN_00452898` for redraw when the marker is not
  `0xFF`.
- `FUN_00453B13` calls `FUN_0045218F` over the view rectangle derived from
  `+0x14/+0x18` dimensions.

These functions update the battlefield display/animation surface. They do not
write actor HP, MP, or status fields. The actual persistence target remains in
the result helper/controller chain below `FUN_004404BD`, separate from view
refresh.
