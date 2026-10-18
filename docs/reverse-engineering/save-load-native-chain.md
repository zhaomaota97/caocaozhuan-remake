# 原版存档加载链

静态入口：`0x41AD06(this, slot)`，由存档确认流程调用。slot 必须为 0..9；文件名通过 `slot + 1` 和窗口对象内的 0x32 字节槽记录拼接。

加载流程：

1. 打开槽文件并读入对象头；首字节必须为 5，否则显示错误并返回 0。
2. 读取 `0x56DC` 字节主存档缓冲区；复制配置区、BGM/环境区和 `0x2DA` 后的映射表。
3. 从偏移 `0x14DC` 开始调用 `0x409188` 512 次，恢复武将/单位表；这与现有 slot8 导出工具完全一致。
4. 调用 `0x42B81B(0x0E)` 切换加载状态，按 slot 再读场景/战场关联文件，随后调用 `0x4F6E6`/`0x4F5BE` 处理附加数据。
5. 设置全局存档状态位并刷新场景；失败时走 `0x474619` / `0x47650F` 的错误/恢复 UI 分支。

保存入口 `0x41B16A(this,slot)` 反向构造同一结构：写入头字节 5、配置区、映射区、128 个 0x40 字节记录和 512 个 0x48 字节单位记录，再写主存档与场景附加文件。现有 `verify_save_objects_native.py` 和 `verify_battle_save_native.py` 已对这些内部记录完成 round-trip 验证。

## 实机崩溃范围

真实 UI 运行中，slot8 行选择消息已经确认成功（列表选择返回 1，命中行 8），随后进入第二层确认框；原版在确认后的加载路径访问 `0xC0C0C0C0`。从 `0x41AD06` 的流程看，崩溃发生在主存档读取之后或附加场景文件读取/刷新阶段，而不是列表控件选择阶段。当前运行目录的 slot 文件与原始窗口内部槽名仍需逐字节核对，不能把该异常归因于重制项目或声称原版存档损坏。

证据：`analysis/native-main/pseudocode/0041ad06.c`、`0041b16a.c`、`analysis/live-startup-20261017-161503/events.jsonl`。动态探针尚未成功捕获 `0x41AD06` 返回值和各个附加文件读取结果；下一步应在该入口和 `CreateFileA` 同时记录 slot 文件路径、读取长度和返回码。

## 实机文件序列

同一日志已经记录到实际窗口路径的文件访问顺序：读取列表阶段会依次打开 `SV00D.E5S`/`SV00S.E5S` 至 `SV09D.E5S`/`SV09S.E5S`，即 10 个存档槽的 D/S 文件都被扫描；slot 8 的行参数为内部值 8、显示编号 9。此前“确认后崩溃”发生在这些文件扫描之后，不能直接把异常归因于 `SV08` 文件本身。

在日志中，`0x41AD06` 入口事件参数为 `0x8`，但没有对应的 native-return，随后出现原版 `0xC0C0C0C0` 访问异常。这证明入口确实收到了 slot 8，但当前探针尚未能把异常前的内部读取阶段拆成成功/失败返回。所有实际路径已保留在 `events.jsonl`，后续应再对 `ReadFile`/`SetFilePointer` 加钩子记录长度和返回值。

## 文件 I/O 动态补充

观测器现已加入 `ReadFile` 和 `SetFilePointer` 钩子。运行 `analysis/live-startup-20261017-161836/events.jsonl` 捕获到：`SV00D.E5S` 读取 49 字节、`SV00S.E5S` 读取 50 字节，以及 `SV08D.E5S` 读取 49 字节、`SV08S.E5S` 读取 50 字节，全部返回成功。这说明存档列表扫描阶段确实读取了 slot8 的 D/S 头部，文件句柄和返回长度均有效；尚未捕获到确认后主数据 `0x56DC` 字节读取的完整记录，因为本轮未稳定进入确认后的加载分支。
Additional file facts from the runtime copy: `SV08D.E5S` is 21,724 bytes and `SV08S.E5S` is 5,891 bytes. The list scan reads exactly 49 and 50 bytes from their headers; those reads return success. These sizes and hashes are recorded in the runtime evidence, but they do not prove the post-confirmation `0x56DC` main-save buffer was accepted.
