# Item presentation timer chain

Native `0x403340 -> 0x42C45F` sets an absolute deadline using
`0x47EB97 = floor(GetTickCount()/50)`. `0x42C4E0` pumps messages until
`0x42F7F0` reports no remaining ticks. Unlike `0x42C4CB`, this entry does
not double its parameter. Twenty native cases (waits 0/1/5/10/255 and
elapsed work 0/1/3/10) match the Web deadline helper. Only clock and message
pump are controlled; original deadline setup and loop execute.

Static item presentation `0x41C762` uses direct waits 5, 10, then sixteen
waits of 1 for blend frames 0..15. These sum to 31 clock ticks. They must
not become doubled 100ms units or generic easing. However, 31*50ms is not
a claim of exact visible wall-clock duration: tick quantization, drawing,
message processing and optional Meff effects can affect observed duration.
The sequence is static call evidence; this probe executes its timer helpers,
not the full drawing routine. Web stage data is separate from live playback.

Reproduce: `python tools/verify_item_wait_chain_native.py` in reverse
workspace. Evidence: `native-item-wait-chain.json`.
