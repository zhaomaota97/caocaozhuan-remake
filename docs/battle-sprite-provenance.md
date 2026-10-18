# 战场单位 Sprite 来源

战场单位的 `art` 索引来自原版 native 渲染流程，而不是角色表 ID：

1. 读取 `Sv08s.e5s` 的 26 字节 actor 记录。
2. 调用原版 `0x442E26` actor 反序列化。
3. 调用原版 `0x3FC48` (`sprite(actor)`) 得到最终 bank index。
4. 使用原版 `Unit_mov.e5` 对应 entry 渲染单位。
5. actor `+0x0D` 的 bit `0x08` 传给原版 mirror 函数，迁移为新项目的 `mirror` 字段。

这些结果来自 `analysis/saved-unit-scenes/manifest.json` 和 `tools/render_saved_units_native.py`，已经转换到 `data/battle-map-31.json`。动画 tile 的时序仍未假设；新项目当前只使用经过证据支持的固定帧。
