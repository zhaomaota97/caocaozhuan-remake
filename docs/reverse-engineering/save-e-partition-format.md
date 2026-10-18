# E 分区格式与加载器

`SV??E.E5S` 不是无版本随机数据，而是由独立对象 `DAT_00492F90` 管理的事件/场景分区。原版读取函数 `0x417A54(this, stream)` 从流版本/模式参数 2 开始，逐项读取：

- 115（`0x73`）条记录，每条在对象表中占 `0x40` 字节，字段布局为 4、1、1、4、1、2、1、1 字节，合计 15 字节散布在记录内；
- 对象内部 `+0x3D10` 的 `0x181` 字节块；`+0x3D0E/+0x3D0F` 两个字节；`+0x3D04` 的 8 字节；
- `+0x38` 起的 0x800 个 4 字节值（8192 字节）；`+0x2038/+0x203C` 两个 4 字节值；
- 末尾 10 字节辅助字段，经 `0x410506` 解释。

写出函数 `0x417C84` 以模式 1 写回同一布局。战场加载入口 `0x41AD06` 读取主存档后调用 `0x417A54(&DAT_00492F90, local_120)`；保存入口 `0x41B16A` 通过 `0x417C84` 写回。因此 E 分区首字节为 0 并不能解释为版本无效，它由自己的流模式控制，不使用 D/S 的首字节 5 约定。

随后 `0x44F6E6` 将 E 分区缓冲区从偏移 `0x23` 交给 `0x44F384`，再恢复 115 个战场演员和 0x640 字节占用图；反向的 `0x44F5BE` 构造首字节 5 的临时战场缓冲区，写入演员和占用图。这是 E 分区与战场运行时对象之间的明确桥接。

文件 `SV08E.E5S` 大小 10,330 字节，与该对象布局的固定大块和末尾字段一致。需要注意：`0x417A54` 的“流模式”参数与文件首字节不是同一个字段，不能用 `SV08E` 的首字节 0 推断加载失败。

长度已逐项闭合：`0x73 * 15 + 0x181 + 2 + 8 + 0x800 * 4 + 8 + 10 = 10330`。新增 `tools/export_e_partition.py`，运行 `python tools/export_e_partition.py analysis/runtime-game/SV08E.E5S` 可生成同目录 JSON，输出 115 条记录、0x181 字节块、两个单字节字段、8 字节块、2048 个 32 位值、两个尾部 32 位值和 10 字节辅助字段。slot8 实际输出为 `analysis/runtime-game/SV08E.E5S.json`，每个字段保留原始小端数值或十六进制块，不给未命名字段添加业务含义。

证据：`analysis/native-main/pseudocode/00417a54.c`、`00417c84.c`、`0044f6e6.c`、`0044f5be.c`、`0041ad06.c`、`0041b16a.c`。尚未对 slot8 E 分区做完整原版 round-trip 动态测试；现有 1,160/1,160 战场保存验证覆盖 D/S 相关结构，E 分区应增加独立验证。
Round-trip proof: `python tools/verify_e_partition_roundtrip.py analysis/runtime-game/SV08E.E5S` reproduces all 10,330 bytes exactly, including all 115 records and fixed blocks. This proves boundaries and serialization order, not business semantics for unnamed fields.
All ten available partitions `SV00E.E5S` through `SV09E.E5S` now pass the same byte-exact round-trip: 10/10 files, each 10,330 bytes and 115 records. The structure is therefore stable across slots, while field semantics remain intentionally unnamed where evidence is absent.
Readable JSON exports now exist for all ten slots beside the runtime copies: `analysis/runtime-game/SV00E.E5S.json` through `SV09E.E5S.json`. They preserve raw blocks and named structural positions from the native reader without inventing field semantics.
Cross-slot comparison is available at `analysis/e-partition-field-differences.json`. All 115 structural records have at least one varying field across SV00-SV09; this supports treating the E partition as live scenario/event state rather than an all-zero template. The comparison intentionally reports values and distinct counts only, without assigning field names.
Field-variation summary is included in `analysis/e-partition-field-differences.json`: `word0`, `byte4`, `byte5`, and `word6` vary in all 115 records; `byte10` and `byte14` vary in 100 records; `byte13` varies in 77; `word11` varies in 39. This is a prioritization signal for future write-site tracing only, not a semantic naming claim.
`tools/summarize_e_partition_ranges.py` writes `analysis/e-partition-value-ranges.json` with min/max/distinct/nonzero counts over all 1,150 records. These are observational ranges only; fields are deliberately not labeled as coordinates, IDs, or dimensions until a native write-site or controlled dynamic mutation confirms that interpretation.

`tools/verify_e_partition_codec.py` now performs a structured encoder round-trip rather than copying input slices. It reads the JSON fields emitted by `export_e_partition.py`, packs each little-endian field and fixed block in the native writer order, and compares the result byte-for-byte with the source. All ten `SV00E.E5S` through `SV09E.E5S` files pass at 10,330 bytes each. This proves the readable field model is lossless for the observed files; it does not assign business meaning to unnamed fields or prove writer behavior for arbitrary out-of-range values.
The final 10-byte auxiliary block is now named by direct native evidence: `0x410506` reads five little-endian uint16 values into object offsets `+0x04`, `+0x08`, `+0x10`, `+0x14`, and `+0x24`; `0x410470` writes the same five values. The exporter exposes them as `auxUint16` and records both function RVAs. Their game-level names remain unresolved.
Important layer distinction: `0x417A54/0x417C84` serialize the scenario object `DAT_00492F90`, while `0x44F384/0x44F6E6` consume a battle-state view beginning at file/buffer offset `0x23`. The latter prefix is 1266 bytes, followed by 115×26 actor bytes and a 640-byte occupancy view. `tools/export_e_battle_prefix.py` writes `SV08E.E5S.battle-prefix.json` with these offsets and hashes. Do not treat the scenario-object stream and battle-state prefix as one flat record table.
The battle-prefix exporter has now been run for all ten E partitions. Every `SV00E` through `SV09E` contains the same readable prefix sizes: state 1266 bytes, actors 2990 bytes (115×26), occupancy 640 bytes. This confirms a stable battle-state bridge across slots; the remaining E bytes belong to the scenario-object/other payload layers and are not assigned by this parser.
The battle-prefix parser preserves the exact `0x44F384` field mapping: serialized bytes 0-3 copy to object `+0..+3`; bytes 4-9 populate `+8,+C,+D,+E,+F,+11`; bytes 10-11 populate `+4,+5`; bytes 12-13 are widened into object `+0x500/+0x504`; bytes 14-15 form the little-endian value at `+0x4FC`; then 250 five-byte entries follow. This mapping is distinct from the scenario object fields read by `0x417A54`.
`tools/verify_e_battle_prefix.py` checks the fixed battle prefix boundary for all ten files: offset `0x23`, length 4,896 bytes (`1266 + 2990 + 640`), ending at `0x1343`; all 10/10 files pass without truncation.
