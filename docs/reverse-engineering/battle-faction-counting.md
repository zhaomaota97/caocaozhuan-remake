# Battle faction/status counting used by EEX conditions

Several EEX handlers call `0x44C658` or `0x44C74D` before reading script
slots. These functions are shared state predicates, not simple HP checks.

## Record fields

For each of the 115 battle actor records, `0x418C90(record)` reads byte
`record+0x0C` as the actor status class. Only status class `2` participates
in the count. `0x43FC1A(record)` reads byte `record+0x05`; values 0-3 are
faction IDs, while values 4 or higher normalize to faction 0.

## Predicate 0x44C658

When its mode byte `object+1` is nonzero, it returns true immediately.
In mode zero it scans records 35 through 115 (indices `0x23..0x73`), and
for each status-class-2 actor calls scenario lookup `0x44F7D0`. If a matching
scenario record exists, it clears/updates the scenario state through
`0x44F840` and returns 1. Otherwise it invokes `0x44C8E6(5,0,0,0,0,0)`;
if that broader predicate returns zero it calls the same scenario update and
returns 1, else returns 0.

## Predicate 0x44C74D

Mode nonzero also returns 1 immediately. In mode zero it first scans all 36
records (indices `0..0x23`) for status class 2 and scenario lookup
`0x44F860`; a match calls `0x44F880` and returns 1. If no such match exists,
it tests the first scenario unit and then counts status-class-1/2 records in
the first 16 entries. With no such records it calls `0x44F880` and returns
1. Otherwise it evaluates `0x44C8E6(0,0,0,0,0,0)` and performs the same
update only when that predicate returns zero.

## Shared counter 0x44C8E6

With `param2 == 0`, it scans all 115 records. With `param2 == 1`, it scans
the coordinate rectangle `[param3..param5] × [param4..param6]` using the
occupancy map. It counts only status-class-2 actors and applies `param1`:

| `param1` | Counted faction |
|---:|---|
| 0-3 | exact normalized faction |
| 4 | factions 0 or 1 |
| 5 | factions 2 or 3 |
| 6 | every faction |

This establishes the static condition semantics used by the EEX handlers;
it does not yet execute the entire victory/defeat transition with an
unmodified live battle. The scenario update functions write script slots 5
and 6 through `0x410077`, which is why opcode 66/67 refreshes are coupled to
these predicates.
