# Live UI sound observation

The live observer was made compatible with the installed Frida runtime by
resolving exports through the owning loaded module rather than assuming the
legacy global-export API. A bounded startup run now reaches the native sound
wrapper and captures:

| Event | Native path | Flags | Native wrapper backtrace |
|---|---|---:|---|
| Startup/menu sound | `SE00.WAV` | 19 | `0x47493d -> 0x4746c4 -> 0x471ccd -> 0x4719af` |

Raw evidence is in `analysis/live-startup-20261018-043509/events.jsonl`.

The observer still records an access violation when attempting to force the
legacy save-list UI in this run, so no select/cancel ID is inferred from that
attempt. The captured startup event proves the hook is live and the wrapper
path is observable; menu-event correlation remains open until a stable save
row activation is obtained.
