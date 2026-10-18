# Live battle surface and control inventory

Trace: `analysis/live-startup-20261018-103542`

Slot 8 loading reached the native completion boundary and exposed the battle window. The visible child-control inventory includes `SoldierFace`, `SoldierChar`, `Effect`, `Influence`, `ButaiSlct`, `GoButaiSlct`, `NamePut`, `Practice`, `MgcEffect`, `MgcInfluence`, `PracMesBox`, `TokugiEff`, `TokugiInf`, `HexTurnName`, `HexMapName`, and `Weather`, plus a ten-button toolbar. This is dynamic evidence of the battle presentation/control surface, not inferred from static resources. The optional movement click was not counted because the process reached the surface after the observer's action phase; the next probe should schedule the click after `battle-surface-detected`.
