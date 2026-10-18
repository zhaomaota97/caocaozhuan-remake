# Live resource load summary

The live event stream from `analysis/live-startup-20261018-044334` was
normalized with `tools/summarize_live_resources.py`.

- Unique file paths observed: `17`
- EEX script loaded: `R_00.EEX`
- DATA.E5 requests: entries `0..5`
- Map/scene resources observed: `MMAP.E5[70]`, `PMAP.E5[30]`,
  `PMAPOBJ.E5[0,1,314,315,338..341]`, `PMPALET.E5[70]`, `UNIT_MOV.E5[108]`
- Other observed containers: `FACE.E5`, `HITAREA.E5`, `IMSG.E5`, `MARK.E5`,
  `LOGO.E5`, `LOGO_P.E5`
- Sounds observed: `SE00.WAV`, `SE_E_01.WAV`
- Resource DLLs observed: `CmdIcon.dll`, `ItemIcon.dll`, `MgcIcon.dll`

Machine-readable output is stored beside the raw event stream as
`live-resource-summary.json`. This is runtime file/resource evidence, not just
a filename inventory.
