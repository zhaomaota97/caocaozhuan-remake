# Status removal item controller

Original chain `0x41DC43 -> 0x41CF61 -> 0x418DA0` was executed for five
status-removal categories, all 256 status bytes and selected/cancelled
targets: **2,560/2,560** matched. The target selector and presentation-success
callback are controlled; free-use skips stock decrement, refresh is suppressed.
The initializer, eligibility, category dispatch and bit clearing remain live.
The process is never resumed into native UI or audio.

| Category | Bits cleared from actor status +0x1E |
| --- | --- |
| 65 | 8 |
| 66 | 16 |
| 67 | 2 |
| 68 | 4 |
| 69 | 30 |

The separate actor/visual flag byte `+0x0D` stays 165 throughout every case.
Cancelled target selection leaves status unchanged and returns zero. Mode
zero eligibility permits clearing an absent bit; this probe confirms that
selected no-op clears can return success with controlled presentation.
It does not claim real UI availability or actual animation was exercised.

Readable rule: `src/rules/statusItemWriteback.ts`; evidence:
`native-status-item-controller.json`. Reproduce in the reverse workspace:
`python tools/verify_status_item_controller_native.py`.
Live Web status-item execution, stock and presentation still need integration.
