# Live new-game battle observation

Run:

```powershell
python tools/observe_live_game.py --start-new --advance-story --seconds 30 --skip-intro --probe-toolbar
```

Evidence directory: `analysis/live-startup-20261018-043631`.

The bounded run reached the battle window and produced native runtime events.
Observed sound dispatches include:

| Native path | Flags | Wrapper caller | Context |
|---|---:|---|---|
| `SE00.WAV` | 19 | `0x47493d -> 0x4746c4` | startup/menu playback |
| `SE_E_01.WAV` | 11 | `0x4749ba -> 0x4746e3 -> 0x474a28` | in-game startup/battle flow |

The same run captured live EEX handler entries for 15 distinct opcodes:
`2, 8, 9, 10, 20, 28, 35, 39, 47, 48, 50, 51, 58, 59, 62`, with handler
RVAs and cursor fields. The newly observed opcodes `2, 8, 10, 39, 47, 58,
59, 62` upgrade the EEX coverage matrix from 21 to 28 dynamic opcode slots.
This is direct runtime evidence that these handlers execute during new-game
setup; it does not assign their complete story semantics by itself.

The raw event stream is `events.jsonl` in the evidence directory. The normalized
opcode evidence is `analysis/native-eex-live-new-game-validation.json`. Toolbar
probing was requested, but no separate per-button sound identity is claimed
because the run did not produce a stable button-by-button event boundary.
