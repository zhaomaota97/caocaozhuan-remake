# 曹操传重制版

独立本地浏览器项目，运行时只使用本目录内的代码、JSON、地图、美术、动画、音乐和音效。

```powershell
npm install
npm run dev
```

## Reverse-Verified Runtime

The source-to-runtime mapping is documented in `docs/reverse-runtime-integration.md`.

## Verification

The only supported development server is `http://127.0.0.1:5173/`.

```powershell
npm run verify:all
npm run test:reverse-rules
npm run verify:independent
npm run verify:resources
```

`REVERSE-STATUS.md`, `FINAL-AUDIT.md`, and `docs/reverse-engineering/` record
what is native-verified, what is migrated but not fully wired, and what remains
open. The project bundles raw extracted assets under
`public/assets/native-extracted/` and does not require the source directory at
runtime.

- Fixed logical canvas: 1120x640; battlefield cells and unit sprites keep native pixel sizes.
- Battle map 31 uses the recovered terrain, actor coordinates, movement frames, idle frames, target shapes and save data.
- The minimap is an external right-side panel. It shows player/enemy and acted/not-acted states, plus the current camera viewport; clicking it scrolls the battlefield.
- The action menu uses recovered command icons. Strategy and item submenus are populated from the recovered effect-learning and equipment records.
- Strategy previews expose the verified effect resource, entry, sound and timeline metadata. `Mcall00..08` visuals and `Se_m_XX.wav` sounds are loaded only where the recovered mapping provides them.
- Native results that are not yet fully recovered remain explicit in the UI instead of being replaced with guessed damage or status rules.

当前战场原型使用逆向后的地图 31、20x32 网格、真实 actor 坐标、单位动画索引、151 套移动帧、原版 BGM 和 `Se_m_XX.wav` 音效。存档使用浏览器 `localStorage`，不读取原版 `.e5/.e5s/.eex`。
