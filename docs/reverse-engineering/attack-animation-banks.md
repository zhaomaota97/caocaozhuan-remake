# Attack Animation Banks

`tools/verify_attack_banks_native.py` invokes the original attack-bank selector and compares the selected decoded artwork against the resource-bank hashes. The current validation covers 151 unit/character indices × 4 facing directions = 604 cases, with 604/604 exact matches (`analysis/native-attack-bank-validation.json`).

The selector is the base animation-bank path used by both ordinary and critical attacks. Critical probability is decided separately in `0x4404BD`/`0x41C4E9`; the selected base bank does not itself encode the critical probability. The critical flash/effect is emitted by the later result-render path, which is why bank selection and the special critical visual are separate reverse-engineering targets.
