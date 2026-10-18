# 剧本到BGM文件的原生映射

## 指令规则

EEX opcode36的handler `0x41581C` 读取tag9：

- 参数255：公共记录`0x4B0770+4`写FF，调用`0x474619`停止音乐。
- 其他参数：调用`0x4745FE(audio,parameter+2)`。此handler自身不写公共记录+4；实际音频控制器的后续状态更新不能省略。

不是用地图ID直接当曲目号。各关脚本可在增援、剧情转折和后续段落内多次切换，完整播放器必须随EEX执行顺序触发。

## 全语料交叉验证

```powershell
python tools/export_script_music_events_native.py
```

117个R/S脚本的全部静态opcode36出现位置共598条，逐条与原始文件字节相等，再实际执行原版分派器和handler；play/stop边界用回调替代避免声音。598/598通过，检查返回值、消费长度、调用参数及公共音乐字节。

其中146条位于S脚本，273条为停止请求。每条记录保留脚本、segment、branch、offset、原参数、原生track、嵌套条件、音频路径及验证结果。

原生track到文件的连接来自另一份已完成的MP3Serv消息处理器验证 `native-music-mapping-validation.json`，没有根据文件名猜索引。全部有播放文件关联的节点，其Web音频文件均存在（缺失数0）。这些只是文件存在检查，不证明所有音乐都已在Web实际触发播放。

输出：`analysis/script-music-events.json`；独立同步到remake `data/mappings/script-music-events.json`。

## S_00的三个明确节点

| segment/branch | offset | EEX值 | 原生track | 文件/动作 |
|---|---:|---:|---:|---|
| 0/0 | 6380 | 6 | 8 | `SoundTrk/08-AudioTrack 08.mp3` |
| 1/2 | 10999 | 5 | 7 | `SoundTrk/07-AudioTrack 07.mp3` |
| 2/0 | 15481 | 255 | 无 | 停止 |

开场音乐位于地图切换后的原始指令序列；增援音乐位于曹操相关事件分支，不应由“点击一个单位”触发。Web中的新关卡控制器必须按这些节点执行，不能用统一默认BGM替代。

## 尚未证明

静态出现位置不等于实际运行可达次数。598条没有覆盖完整剧情条件、音频设备、异步切换/停止时序、Koeicda/MP3Serv运行中的状态反馈或浏览器有声自动播放限制。播放器在关卡中真正执行这些指令、循环/音量和资源加载时序仍需接入验证。
