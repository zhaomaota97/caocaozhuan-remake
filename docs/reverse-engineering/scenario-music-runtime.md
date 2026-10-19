# Scenario BGM runtime integration

The static/native music export contains 598 verified play/stop events. The
first play event for each `S_00.eex` through `S_57.eex` is now indexed in
`data/mappings/scenario-music.json`; all 58 mappings point to existing Web
MP3 assets and preserve the native track number and source offset.

`BattleScene` preloads the mapped tracks and starts the current scenario's
track when the scene begins. This replaces the previous S_00-only hardcoded
track 8 behavior. Scene initialization and shutdown destroy all scenario
music instances so restarting a map cannot layer multiple BGM streams.

This ports the first script play event. Later conditional script changes
and stop/switch events remain part of the incomplete EEX runtime; this is not
a claim that a whole scenario's music timeline has been executed.
