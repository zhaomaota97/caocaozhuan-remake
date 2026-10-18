# 地图与存档 codec 验证

本轮使用实际工具名称复跑原版 codec：

- `python tools/verify_map_readers_native.py`：132 个地图、784,646 个读取结果全部匹配。
- `python tools/verify_save_objects_native.py`：5,120 个对象 round-trip 全部匹配。
- `python tools/verify_battle_save_native.py`：1,160 个战场存档 round-trip 全部匹配。

这些结果覆盖地图读取、普通存档对象和战场存档对象的原版序列化/反序列化。它们与 `analysis/game-format-inventory.json`、`analysis/native-map-reader-validation.json`、`analysis/native-save-object-validation.json` 和 `analysis/native-battle-save-validation.json` 相互对应；验证基准是原始文件字节和原版函数结果。

范围边界：codec round-trip 证明结构化字段和字节布局可复现，不证明所有文件里的剧情语义、压缩外层、运行时校验错误提示或 UI 保存流程都已迁移。UI 命令链另由 `verify_ui_save_chain.py` 验证，原版保存命令 101、读取命令 102 和设置命令 107 均已确认。
