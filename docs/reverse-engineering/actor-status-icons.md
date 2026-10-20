# Native status icon rendering

Original renderer `0x43EB1F` now has 512 captured cases crossing actor flags
0/6, status bytes 0..31 and phases 0..7. Tile provider, actor draw, icon draw
and resource-buffer lookup are controlled; original phase/flag/status branches
and indexed color transforms execute. The probe records 16x16 icon draw
coordinates/resource offsets and the final actor pixel buffer prefix.
Web icon selection and composed actor pixels match every captured case.

Single statuses 2/4/8 select resource-buffer offsets 0x1A4C0/0x1A3C0/0x1A2C0
and alternate x=4/28 with phase parity. Multiple states display one icon per
phase, not a row: status mask 6 alternates offsets 0x1A3C0/0x1A4C0; mask 10
alternates 0x1A4C0/0x1A2C0; mask 12 alternates 0x1A3C0/0x1A2C0; mask 14
alternates 0x1A4C0/0x1A2C0. Their x positions are 28/4. All use y=0 and
draw mode 4, relative to actor tile top-left. This explicit native priority
must not be replaced with an invented all-status icon layout.

This also supplies dynamic renderer evidence for the status-bit-16 phase
color gate and darken-before-status composition. Native icon image extraction
and live Web overlay sprites remain unfinished. The controlled resource-buffer
query proves offsets, not which original archive entries populate them.

Reproduce: `python tools/capture_actor_status_icons_native.py` in reverse
workspace. Evidence: `native-actor-status-icons.json`.
