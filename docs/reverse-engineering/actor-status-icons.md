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

Resource loading is now identified: native `0x42BA29` reads raw `Mark.e5`
from file offset zero for exactly 0x1C7E0 bytes into the shared marker buffer.
The file has that exact length; each recorded icon offset therefore resolves
directly to 256 original pixel bytes. All three extracted source-color sets
match across the 58 Spalet records. `status-icon-art.json` records source
offsets and pixel SHA-256; the browser uses original 16x16 transparent images.

Live overlays follow the verified phase selection and tile-relative positions,
hide for absent status/dead/deferred actors, and are suppressed while actors
are in movement/attack presentation. This supersedes the earlier extraction
and overlay integration gap. Ordinary idle overlays are covered by browser
position/resource tests; exact full presentation overlay visibility still
needs native presentation-specific traces. Actual icon bytes are hash-checked
against the independently migrated raw MARK file. Export tool:
`python tools/export_status_icon_art.py` in reverse workspace.
