# EEX 动态启动边界

运行 `observe_live_game.py --skip-intro --seconds 20` 得到的目录
`analysis/live-startup-20261017-022629` 记录了以下顺序：

1. `SVCMN.E5S` 被打开；
2. `DATA.E5` 条目 `0,1,2,3,4,2,5` 被实际请求（重复请求保留在原始日志中）；
3. 主窗口控件已创建，但尚未出现剧情菜单；
4. `0x4109EF` EEX dispatcher hook 捕获 0 次；
5. 进程随后因 `ntdll.dll` 读取 `0xC0C0C0C0` 的访问冲突终止。

这条证据把当前动态边界定位为“DATA/SVCMN 初始化 -> 主窗口创建”阶段。它证明正常启动尚未执行 EEX dispatcher；不能用它推断剧情脚本没有运行，只能说明本次崩溃发生在剧情入口之前。

后续消息层 hook 进一步确认：启动阶段通过 `SendMessageW`/`PostMessageW` 发送窗口消息，而不是调用 `DispatchMessageW`。运行目录 `analysis/live-startup-20261017-024258` 共捕获 127 条消息，最早的自定义消息号包括 `641` 和 `642`。因此后续剧情入口自动化应从这条消息路径和主窗口控件入手。

在 `analysis/live-startup-20261017-024459` 中，消息 hook 已解析窗口类和标题：`641/642` 主要发给主窗口类/标题“ 三国志曹操传 ”以及 `SmallMap`/“战场缩小图”，并伴随 `wParam` 1/2 和 `lParam` 0 或 `0xC000000F`。这组消息属于窗口/小地图初始化，不能直接当作 EEX opcode。
