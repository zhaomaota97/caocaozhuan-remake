# Manual item growth and status controllers

Native dispatcher `0x41DC43` routes manual item categories as follows:

- `0x41..0x45` -> `0x41CF61`: resolves the target, checks `0x41C4E9`,
  plays the item presentation through `0x41C762`, then writes one of the
  native actor flags `0x08`, `0x10`, `0x02`, `0x04`, or `0x1E` through
  `0x418DA0`.
- `0x46..0x4A` -> `0x41D080`: reads the target's growth/stat values, computes
  saturated deltas using the native helper, renders the item presentation,
  writes the resulting unit attributes, and calls `0x43F98E` to update the
  corresponding actor field. The five branches use distinct native fields and
  resource markers (`0x22` through `0x25` in the presentation path).

This is enough to distinguish the stat-fruit family from equipment and from
HP/MP consumables. It is not enough to implement an exact Web result yet:
the field-to-attribute mapping, level/maximum clamps, inventory decrement
ordering, and target eligibility need dynamic controller probes. The Web port
therefore keeps these result writes deferred rather than substituting generic
`+2` stat behavior from the item table alone.
