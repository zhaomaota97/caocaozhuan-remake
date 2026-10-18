# EEX Battle Setup Dynamic Validation

The native EEX setup probes now cover the pre-action battle state used by story scripts:

- Enemy setup: 24/24 contexts and 480 actor records.
- Branch selection: 12/12 conditions.
- Unit-count handler: 6,144/6,144 cases.
- Unit restoration: 288/288 contexts.

These results establish the tested EEX-to-battle setup and branch predicates. They do not claim that every AI action or complete story playthrough has been dynamically captured; the remaining integration gap is the full turn trace from setup through target scoring, action execution, and victory/defeat dispatch.
