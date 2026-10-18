# EEX 副作用与剧情分发验证

本轮执行：

- `python tools/verify_eex_side_effect_native.py`：opcode 7 的设置、清除、运行时默认和 mode-3 分支全部通过；确认 handler `0x415C46` 与 opcode 106 handler `0x416DFA` 的差异化写回。
- `python tools/verify_eex_side_effect_candidates.py`：7 个候选 opcode 的全局状态写入地址与静态候选集合全部通过。覆盖 opcode 6、7、39、69、91、93、106。
- `python tools/verify_eex_dispatch_native.py`：59/59 个 dispatcher 分支通过原版调用验证。

结果写回到现有 `analysis/native-eex-*` 清单。EEX 脚本不是单纯文本：opcode dispatcher 根据记录类型调用 handler，handler 会读取运行时模式并修改全局状态、角色/场景数据或分支变量。opcode 7 的动态测试明确显示同一 opcode 在不同模式下可以写入 0，也可以保留运行时值；重制实现不能把每条脚本记录简单转换为固定赋值。

本轮只验证副作用地址、dispatcher 和代表性 opcode 的状态变化，未声称所有 opcode 的完整语义、剧情条件组合和存档持久化已经恢复。可读脚本文本位于 `analysis/story-readable/`，机器证据位于 `analysis/eex-bodies/` 与 `analysis/native-eex-*`。
