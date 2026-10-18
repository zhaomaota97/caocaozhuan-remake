# 新游戏剧情 EEX 动态入口

运行：

```powershell
python tools/observe_live_game.py --skip-intro --start-new --seconds 30
```

证据目录：`analysis/live-startup-20261017-025202`。

结果：

* 主菜单控件 `id=1027`（开始新游戏）被自动点击；
* 日志捕获 `start-new=1`；
* 捕获 `eex-dispatch=26`；
* 随剧情初始化加载 `SVCMN.E5S`、`PMAP.E5`、`PMPALET.E5`、`PMAPOBJ.E5`；
* 代表性 dispatcher 调用参数：`arg2=0x410210`、`arg2=0x4100DB`，解释器上下文为 `ECX=0x492F90`。

这证明主菜单新游戏入口已经能够进入 EEX 解释器。当前 hook 记录的是 dispatcher 原始参数和上下文，尚未把参数指针完整解码成 opcode/脚本偏移；下一步将根据 `0x410273`/`0x4109EF` 的调用约定读取指令游标和脚本文件名。

进一步 hook `0x410273` 解释器入口后，在 `analysis/live-startup-20261017-025536` 捕获到 1 次真实解释器调用：`ECX=0x492F90`，`param1=0x03BE04A0`。这确认 dispatcher 到 interpreter 的调用链；下一轮将把该参数对象按 `0x410273` 的字段布局解码。

在 `analysis/live-startup-20261017-025922` 中，解释器内存快照已成功序列化：`param1=0x03D004A0`，前四字节为 `EEX\0`，首 16 字节为 `454558000102000000000e0000000100`，小端 16 位字段为 `[513,0,0,14,0,1]`，偏移 `0x10` 的首个 16 位值为 `2682`。复现工具为 `tools/parse_live_eex_events.py`。

在 `analysis/live-startup-20261017-030423` 中，解释器前后快照成对捕获。返回后 `this+0x20=0x03DA04A0` 保留原 EEX 参数对象，`this+0x1C=0x03DB1C00`、`this+0x0C=0x03DA04AE`、`this+0x28=1`、`this+0x30=10`。这证明 `this+0x20` 是当前脚本消息指针，`this+0x1C`/`+0x0C` 是解释器执行期间更新的游标/状态指针候选。复现工具为 `tools/summarize_live_eex_state.py`。

参数对象前 16 字节显示：偏移 `0x0E` 的值为 `1`，偏移 `0x10` 的值为 `2682`。因此 `this+0x0C = param1+0x0E` 指向的值很可能是第一条控制 opcode/分支类型，而 `0x10` 是其后续长度或参数字段；`tools/parse_live_eex_events.py` 现在同时输出这两个候选值。

最新运行目录 `analysis/live-startup-20261017-032828` 已直接验证指针关系：返回时 `cursor_ptr=0x03EF04AE`，而 `param1=0x03EF04A0`，正好相差 `0x0E`；游标处 32 字节为 `01 00 7A 0A 02 00 05 00 ...`。`state_ptr=0x03F01C00` 指向状态指针数组，前四项分别指向 `0x03F01C20`、`0x03F01C30`、`0x03F01C40`、`0x03F01C50`。这将 EEX 解释器游标和状态表从推测提升为运行时指针证据。

文件映射已确认：运行时快照前 128 字节与磁盘 `R_00.eex` 前 128 字节完全一致，其他 116 个 `.eex` 文件均未匹配该前缀。因此新游戏剧情入口当前加载的是 `R_00.eex`，不是泛化推测。该结果可由 `analysis/live-startup-20261017-025922/events.jsonl` 和 `R_00.eex` 复核。
Runtime verification (2026-10-17 03:39:57, `analysis/live-startup-20261017-033957`) is reproducible with `tools/verify_live_eex_alignment.py`: interpreter enter/return are both 1; the runtime buffer prefix matches `R_00.eex` byte-for-byte; on return the cursor is exactly `param1 + 0x0e` and its first four bytes equal the file header cursor field. The run recorded 26 dispatcher entries and 25 returns, so one startup dispatch path still needs stack/exception correlation.

The follow-up run `analysis/live-startup-20261017-034209` adds accurate return addresses and backtraces to each dispatcher event. Repeated script dispatches return through `0x4101a5` or `0x41061d`; the recorded unmatched entry is retained for the next exception-path correlation. The alignment verifier remains `4/4`, and the full regression suite remains green.

Run `analysis/live-startup-20261017-034439` additionally snapshots dispatcher arguments. In the `0x4101a5` path, `arg0` is the live interpreter object (`0x492f90`) and its first 32 bytes contain changing script state, while `arg1=0x7787962d` points into executable code bytes (`8b d8 8b c3 ...`). In the `0x41061d` path, `arg0=0x6cfe70` and `arg1=0x6cfe90` are writable state records, while `arg2=0x410210` points into code bytes. This establishes that the dispatcher receives a state record plus a code/context pointer; the numeric `arg2` values are not opcode numbers.

The new verifier `tools/verify_live_eex_node_alignment.py` resolves the interpreter object's `+0x0c` field: subtracting the runtime EEX buffer base yields exact decoded node offsets. In `analysis/live-startup-20261017-034439`, 17/17 instruction dispatches match `R_00.eex` nodes, including offsets 139 (opcode 28), 141 (35), 153 (48), 179 (50), through 535 (20). Two preceding records at offsets 18 and 47 are header/initialization work. This is the first direct dynamic opcode alignment, rather than an inferred file-prefix match.

Native handler hooks in `analysis/live-startup-20261017-034839` directly observed opcode 35 -> `0x4157B4` (one call), opcode 50 -> `0x4132D4` (eight calls), and opcode 20 -> `0x413661` (one call). `tools/summarize_live_eex_handlers.py` reproduces these counts. The handler entry arguments include the interpreter object and the current command selector, providing the first runtime confirmation of static opcode-to-handler mappings.

The rerun `analysis/live-startup-20261017-035007` captured all seven handlers used by this story prefix: opcodes 9, 20, 28, 35, 48, 50, and 51. There were 17 handler calls in total, with no hook errors. `tools/verify_live_eex_handlers.py` confirms `args[1] == opcode` for all 17/17 calls. The observed handler RVAs are 0x15B0F, 0x13661, 0x13EBD, 0x157B4, 0x13010, 0x132D4, and 0x134C9 respectively, directly validating the static opcode index.

Battle runtime run `analysis/live-startup-20261017-035220` loaded map 31 from slot 8 and captured complete pre/post action snapshots. `tools/diff_live_battle_snapshots.py` shows actors, roster, terrain, and artwork unchanged; only one byte in the 1266-byte battle state (offset 11) changed after the click test. No movement entry was observed, so this byte is recorded as a UI/turn-state candidate rather than a confirmed movement field.

`tools/export_battle_actor_grid.py` exports the 115 fixed 26-byte actor records. For the live map-31 snapshot, record offsets +8/+9 decode as grid `pos_x/pos_y`, +7 as side/type, +0/+1 as unit ID, and +14 as status. Active friendly examples are unit 0 at (8,8), unit 23 at (8,4), unit 15 at (8,5), unit 20 at (8,7), and unit 17 at (9,9); inactive records use position 255/255. The decoded table is `analysis/live-startup-20261017-035220/actors-grid.csv`.

The complete active set contains 32 actors: 7 side-0 units and 25 side-2 units, all with status 2. Coordinates are bounded by x=2..13 and y=4..25 inside the 20x32 battle grid, and the opposing formation occupies the lower rows (mostly y=19..25). This spatial distribution and the exact 20x32 terrain buffer provide an additional runtime check that +8/+9 are cell coordinates rather than pixel positions.
