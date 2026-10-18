# Native attacker reward controller

`python tools/verify_attack_reward_controller.py` executes the native
`0x405C6C` controller after its presentation callbacks are replaced with
no-ops. It passes 2,592/2,592 combinations and writes
`native-attack-reward-controller.json`.

The controller takes accumulated unit and weapon reward totals from action
offsets `0x428` and `0x42C`, adds the attacker's current level-based rewards,
then calls unit writeback `0x408950` and equipment writeback `0x4082D6`.
The native controller itself therefore performs the same level/stat growth
and equipment XP transitions independently verified in the other reports.

The probe covers unit IDs 25/26, levels 1/49/50, XP 0/99/255, incoming unit
awards 0/1/100/250, weapon level 0/2/3, weapon XP 0/99/255 and incoming
weapon awards 0/1/100/250. It confirms unit growth only occurs for eligible
IDs and levels, equipment XP is capped by the native item rule, notifications
and refresh callback counts are correct, and the native RNG remains at seed 7.

The controller sets action current target and then invokes the native
presentation function before reward calculations in the full battle loop.
That presentation is stubbed in this probe. The controller's maximum-style
aggregation of multi-target reward totals is statically identified in
`0x405E03`; this single-target controller matrix does not independently
verify all multi-target aggregation permutations.

The probe uses class 0, item 0 as a normal weapon, and resets runtime unit
records between cases. It does not claim that every unit or weapon in the
original scenario uses these exact IDs. It proves the controller's native
writeback boundary and its state transitions for controlled records.
