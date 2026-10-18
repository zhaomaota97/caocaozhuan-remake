# Live EEX opcode union rerun

`tools/summarize_live_eex_runs.py` scanned all bounded
`analysis/live-startup-*/events.jsonl` streams. Across 17 runs, the observed
opcode union is 15 slots:

`2, 8, 9, 10, 20, 28, 35, 39, 47, 48, 50, 51, 58, 59, 62`.

The machine result records the first evidence directory for each opcode and
the per-run sets: `analysis/live-eex-opcode-union.json`. This is a stronger
aggregate dynamic baseline than any single startup run, but it remains partial
coverage of the 106 non-reserved handler bodies.
