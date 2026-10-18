# Story and EEX export rerun

The complete story/script export pipeline was rerun:

- Structured story fields: `9420` from `117` scripts
- CP936 decode errors: `0`
- Private-use fields retained: `15`
- Tag-5 string candidates: `12065`
- Text candidates: `23799`
- EEX branch offsets: `2320/2320` across `117` files
- Opcode index: all `108` slots written
- Corpus usage: `92` used, `16` absent

The exports are lossless evidence indexes; absent corpus usage is not treated as
proof that a handler is unreachable.
