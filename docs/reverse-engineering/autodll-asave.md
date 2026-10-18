# AutoDLL.dll `ASave` 导出

`AutoDLL.dll` 的导出表只有 `ASave` 和 `dummy`。对 `ASave`（RVA `0x12B0`）反汇编显示：

* 入口先检查调用条件；未满足时直接跳转主程序地址 `0x44E1D3`；
* 满足时读取 DLL 全局开关 `0x10009038`；
* 向主程序内部对象/地址 `0x41B1F4`、`0x41B4E7` 写入控制字节和指针；
* 最后跳转主程序地址 `0x44E6EE`。

因此 `ASave` 是自动化/补丁注入跳板，不是独立的 `Sv??d.e5s` 或 `Sv??s.e5s` 编解码器。真正的存档序列化仍由 `Ekd5.exe` 的 `0x408F2E/0x409188` 和战斗状态函数负责。`dummy` 为 1 字节占位函数。

原始证据：

* `analysis/dll-rizin-inventory.json`
* `analysis/dll-calls.csv`
* `rizin` 对 `analysis/runtime-game/AutoDLL.dll` 的 `sym.AutoDLL.dll_ASave` 反汇编

最新反汇编回归确认的关键跳转：

```text
0x100012b2  mov eax, 0x44e1d3
0x100012b7  jmp eax
0x100012c6  jz  0x10001340
0x10001344  mov eax, 0x44e6ee
0x10001349  jmp eax
```
