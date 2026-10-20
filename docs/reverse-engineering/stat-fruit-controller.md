# Stat fruit controller

Native `0x41D080` passes 1,125/1,125 controlled calls. Original initializer,
eligibility, getters/setters, saturation and actor state updater `0x43F98E`
execute. Target selection and item presentation are replaced; stock dispatch
is outside the probe. No native UI/audio runs.

Categories 70/71/72/73/74 map to attribute indexes 0/2/1/3/4. Each increases
unit base byte `+0x15+index` and rank byte `+0x21+index` by floor(itemValue/2),
capped at 255 and 50 respectively. Actor attribute state `+0x18+index`
becomes 3 when previously below 3, otherwise 6, even for zero gain. Other
attribute fields remain unchanged. This state change is required for later
native battle getter recalculation; treating a fruit as a bare fixed stat
increase is incomplete.

Matrix: five categories, values 0/1/2/5/255, stats 10/254/255, ranks 24/49/50,
states 0/2/3/4/6. Web state rules match all outputs. Complete UI, inventory,
notification and actor refresh integration remain open.
Reproduce: `python tools/verify_stat_fruit_controller_native.py` in the
reverse workspace. Evidence: `native-stat-fruit-controller.json`.
