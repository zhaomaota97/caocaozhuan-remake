# Native camera chain findings

## Confirmed call chain

- `0x455123` computes a tile target from two direction/offset bytes and the current camera tile, then calls `0x454CEF`.
- `0x454CEF` performs discrete per-loop stepping toward the target. Each axis advances by `min(4, floor(abs(delta)/4)+1)` tiles and calls `0x454B7E`.
- `0x454B7E(..., mode=0)` commits `scrollX = targetX * 0x30` and `scrollY = targetY * 0x30` and refreshes the viewport. It is not an easing function.
- `0x454B7E(..., mode=1)` additionally clamps against the native map dimensions and current viewport.

## Presentation callers

- Ordinary attack presentation `0x405744` passes the target record's two-byte geometry value and the selected target slot to `0x455123` after facing/damage presentation and before the optional dialogue dispatch.
- Automatic HP item path `0x41CCDF` and `0x41CE3D` also call `0x455123` before their presentation writeback.

## Porting boundary

The stepping algorithm and pixel unit (`0x30`, 48) are confirmed. The exact semantic source of the two-byte geometry value returned by `0x403360`, and the native map dimension units used by `DAT_004B422C/D`, still require a dedicated runtime capture. Web must not invent a smooth camera or generic center-on-unit behavior until those fields are captured.
