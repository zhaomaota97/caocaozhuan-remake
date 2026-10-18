# Battle Toolbar Evidence

Bitmap resource 302 and the fifteen-entry 32-bit TBBUTTON table at 0x48EA78 are used by native creator 0x476063. The table contains twelve buttons and three separators. Each command name is recovered from the original APPMENU resource, not inferred from image appearance.

| Command | Original Menu Label |
|---:|---|
| 104 | 结束游戏 |
| 101 | 保存 |
| 102 | 读取 |
| 107 | 环境设定 |
| 105 | 武将一览 |
| 40147 | 持有道具一览 |
| 40150 | 地形情报一览 |
| 40151 | 宝物图鉴 |
| 109 | 结束回合 |
| 106 | 胜利条件 |
| 108 | 战场缩小图 |
| 110 | 检索未执行部队 |

The standalone scene currently renders these buttons with original labels as tooltips. Their original command handlers are not yet implemented. Earlier hypotheses treating 0x6B as a save command are superseded by this resource mapping: 0x6B (107) is environment settings; save is 101.
