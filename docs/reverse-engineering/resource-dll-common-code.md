# 资源 DLL 共用代码审计

`Cmdicon.dll`、`Itemicon.dll`、`Mapatr.dll`、`Mgcicon.dll` 各自由 Rizin 发现 74 个函数，均只有模块入口级导出，且 `.text` SHA-256 完全相同：

```text
e48333d5c7e7e1fc3e420d4070c8b94f25f258cf14be84d46582b9ecc3c002ff
```

它们的差异来自资源段：图标、地图或菜单图像资源数量不同。当前证据支持把它们视为同一资源加载/窗口代码的四个资源变体，而不是四套独立游戏逻辑。资源 DLL 的业务语义重点应放在资源 ID 到资源段内容的映射；公共代码不需要重复分析四次。

资源数量复核：`Cmdicon.dll` 4 个、`Itemicon.dll` 210 个、`Mapatr.dll` 28 个、`Mgcicon.dll` 62 个；四者资源类型均为 Windows 图像类型 `2`。

证据：`analysis/dll-inventory.json`、`analysis/dll-rizin-inventory.json`、`analysis/dll-resources/`。
