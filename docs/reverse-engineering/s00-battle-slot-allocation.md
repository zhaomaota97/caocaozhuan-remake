# S_00 原生战斗槽分配

## 关键函数

`0x44CC85` 在战场初始化时遍历 `0x492F90 + 0x2044 + stateIndex*0x40` 的场景单位记录，读取 `record[+0x08]` flags：

```text
if (flags & 3) == 0:
    battle slot = primaryCounter; primaryCounter starts 0
else if (flags & 3) == 2:
    battle slot = auxiliaryCounter; auxiliaryCounter starts 15
else:
    battle slot = enemyCounter; enemyCounter starts 35
```

每条记录随后调用 `0x4274C(battleSlot, unitId, flags, record[+4], record[+5])`，将角色、flags、坐标和控制位展开到 `0x4B2C50 + battleSlot*0x24`。辅助/敌军分支还恢复装备、策略、HP/MP等字段。

## S_00 结果（纠正早期25条统计）

S_00 的26条有效记录全部可分配。早期导出把全零记录当空记录，错误排除了角色0曹操；原版空标记是32位值65535，不是全零。该过滤器已移除，以下结果取代此前25条统计：

- 槽15–25：`flags & 3 == 2`，原生 auxiliary-slot-group。
- 槽35–48：`flags & 3 == 1`，原生 enemy-slot-group。
- 槽0：角色0曹操，`flags & 3 == 0`，原生 primary-slot-group。其默认坐标是阶段快照中的值，不代表战前事件执行后的最终出场位置。

完整角色名、坐标、flags、资源索引、槽位和原始记录已写入 `analysis/s00-units-readable.json`，并同步到 remake `data/scenarios/S_00-units-native.json`。脚本 `tools/enrich_s00_units_with_battle_slots.py` 可重复生成。

## 阵营字段边界

这已经是原版实际的战斗槽分组证据，可以安全用于 Web 的初始槽位与阵营组。但报告仍使用 `primary-slot-group`、`auxiliary-slot-group`、`enemy-slot-group` 这些中性名称：原版的 UI/剧本可能把槽15组显示为友军或其他控制侧，不能仅凭槽区间给产品层命名。

`0x406710` 的候选比较读取展开后的 battle slot `+4 < 0x23`，而不是直接读取场景记录 flags。现已定位 `0x442613(this,index)` 直接写入 `slot+4=index`，由 `0x44D427` 的初始化循环逐槽调用。这是槽号，不是独立的阵营枚举；二分比较会把主组和辅助组都归入小于35的一侧。

## 原生交叉验证

```powershell
python tools/verify_s00_slot_allocation_native.py
```

115/115个真实构造函数调用通过：slot+4等于槽号，ID为65535，类型为0，坐标为FF/FF。再恢复opcode70、71以及15个opcode75后的原生状态快照，实际调用 `0x44CC85`，捕获12、26和每次26次初始化调用；槽号、ID、flags、坐标与独立Python投影完全一致，包括opcode75修改后的曹操槽0。

资源加载、角色展开、HP/MP、装备和后续脚本叶函数被替换，以隔离槽分配控制流。因此这验证了分配和槽号构造，不是完整战场初始化或真实剧情执行。结果见 `native-s00-slot-allocation-validation.json`。
