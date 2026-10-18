# Unit experience writeback and growth

Reproduce: `python tools/verify_unit_level_growth.py`.
Latest result: 22,896/22,896 native comparisons matched. Raw evidence:
`native-unit-level-growth.json`.

The test executes original `0x408950` (experience writeback), `0x4073B8`
(level increment), `0x4072FC` (growth rank), and `0x406E17` (stat increase).
Only refresh callback `0x479A01` is replaced. The display parameter is zero,
so level-up presentation and learned-spell presentation are not exercised.

## Experience and level limits

`0x408950(unit, totalExperience, display)` takes the **new total** experience,
not just the award. Its attacker-reward caller `0x405C6C` adds existing
experience before invoking it.

It only updates units with native unit ID below 26 and initial level below
50. Each complete 100 experience calls the level increment function once;
growth is capped at level 50. At a final level below 50 the remainder is
stored in unit byte `+0x2D`; at level 50 that byte becomes 255. An already
level-50 unit is unchanged, including its existing XP byte. Ineligible unit
IDs are also unchanged. Refresh is dispatched once per eligible writeback,
including a writeback that grants no level.

## Growth

Seven class growth bytes come from runtime class record offsets `+2..+8`.
The first five growth amounts are `floor((classGrowth + rankBonus)/2)`.
Rank bonus uses the corresponding unit byte at `+0x21..+0x25`:

| Attribute byte | Bonus |
| --- | --- |
| below 25 | 1 |
| 25 through 34 | 2 |
| 35 through 44 | 3 |
| 45 and above | 4 |

The last two growth amounts use class growth directly. Increases apply to
unit stat bytes `+0x15..+0x19` (cap 255), dword `+0x1C` (cap 500), and byte
`+0x20` (cap 250). They do not depend on random draws in this data path.
The probe also checks that the complete 115-record battle actor array is
unchanged across all calls; current battlefield HP/MP are not refilled by
this non-presentation path.

## Coverage and limits

The matrix covers all 53 class records, unit IDs 25/26 (eligibility edge),
starting levels 1/49/50, rank bytes 24/25/34/35/44/45, experience totals
0/99/100/199/500/1000, and low/near-cap initial stats. Native class growth
bytes are captured as inputs; the independent expected calculation checks
the rank formula, number of increments and stat caps. This is not an
independent validation of class-table parsing from disk.

Not covered: negative/overflowing experience inputs, display-enabled spell
notifications, refresh callback side effects, class changes, or complete
attack reward integration. The initial eligible-ID boundary is verified;
its narrative meaning is not inferred merely from the numeric limit.
