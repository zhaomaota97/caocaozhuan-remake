# Native Animation Command Reader

Run `python tools/verify_animation_command_reader.py`. All 256 opcode-byte
cases match native `0x427F04` and next-pointer helper `0x427F2E`, without
function replacements. The independent expected table comes from PE bytes
at RVA `0x8B9D8`.

| Opcode bytes | Native length-table value |
| --- | --- |
| 0x00-0x07 | 1 |
| 0x10-0x17 | 1 |
| 0xE0 | 2 |
| 0xEF | 1 |
| All others | 255 |

The reader returns the command in its low byte and writes a 16-bit length
to its output pointer. Upper return bits are unspecified and must not be
interpreted as another field. Its output write leaves the following two
bytes untouched, verified using a nonzero guard. The next-pointer helper
adds the returned length literally, including 255 for unknown bytes. A
readable decoder should flag those unknown entries rather than pretending
they are valid 255-byte instructions.

Static caller `0x42A361` couples this stream to the frame-sequence stepper:
it waits while the counter at object+2 is below interval at object+0,
then resets the counter, reads the command at saved stream offset +0x3E,
and advances by the command length. High-nibble-zero commands invoke
`0x42A4F5` with the low nibble (frame advancement plus movement query).
High-nibble-0x10 commands instead set direction at object+0x2E. Byte 0xEF
terminates processing with return 0xFFFF. The isolated reader test does
not validate the complete command runner, tick scheduling, 0xE0 semantics,
resource buffer initialization or final image/sound output.

Raw evidence: `native-animation-command-reader.json`.
