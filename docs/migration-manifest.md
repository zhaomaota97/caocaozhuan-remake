# 已迁移资源清单

所有路径均位于 `caocaozhuan-remake` 自身目录，运行时不访问原项目。

| 类别 | 数量 | 目标 |
|---|---:|---|
| 战斗地图 PNG | 58 | `public/assets/maps/` |
| 移动动画 PNG | 151 | `public/assets/animations/movement/` |
| 攻击动画 PNG | 151 | `public/assets/animations/atk/` |
| 特殊动画 PNG | 151 | `public/assets/animations/spc/` |
| BGM MP3 | 21 | `public/assets/audio/bgm/` |
| 音效 WAV | 37 | `public/assets/audio/` |
| Cmdicon 图标 | 4 | `public/assets/ui/` |
| 资源 DLL 图标 PNG | 304 | `public/assets/ui/dll/` |
| Mcall 效果预览 GIF | 9 | `public/assets/effects/` |
| 保存战场单位场景 PNG | 10 | `public/assets/scenes/` |
| 逆向映射 JSON/CSV | 79 | `data/mappings/` |
| 可读剧情文件 | 119 | `data/stories/` |

攻击/特殊动画已经迁移为透明 PNG。动画帧时序和方向只有在逆向证据充分时才会接入运行时；资源复制不等于擅自推断播放逻辑。
