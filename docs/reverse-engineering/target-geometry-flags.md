# Target geometry flags and Web equivalence

Native `0x436586` was rerun in geometry mode 1. All 320 cases matched:
16 shape slots, high-bit aliases 0/128, include-origin flags 0/1, and five
origins (center and map corners). The native grid is 20 by 32. Both native
grid write sets and the geometry-mode return values are captured in
`native-target-shapes.json`.

`inAttackRange` now accepts the separate native flags argument (default 0).
Bit 0 includes the origin. The range parameter high bit only aliases the
low-seven-bit shape selector; it does not include the origin. Range 255
remains a disabled sentinel even with include-origin enabled.

The Web test enumerates all 640 cells for each captured case and compares
its selected set directly with the native cell set. It also retains the
saved-actor range-selector and ordinary-exchange checks. This verifies
geometry, not enemy/friendly eligibility or the mode-0 target list.

No controller-specific include-origin flag is guessed: existing callers
retain their default until the corresponding native call arguments are
connected. Thus the helper supports the proven flag semantics without
claiming that complete strategy/item target controllers are implemented.

Reproduce native capture in the reverse workspace:

```powershell
python tools/verify_native_target_shapes.py
```

Check the Web implementation:

```powershell
npx playwright test tests/attack-range.spec.ts tests/ordinary-exchange.spec.ts --reporter=line
```
