# Battle Actor Layout

The battle save and live snapshot actor area contains 115 records of 26 bytes each. The runtime map-31 snapshot is `analysis/live-startup-20261017-035220/snapshot-actors.bin`; `tools/export_battle_actor_grid.py` exports it as CSV.

| Offset | Size | Current interpretation | Evidence |
|---:|---:|---|---|
| `0x00` | 2 | Unit ID (little-endian) | Values match roster IDs in active records |
| `0x02..0x05` | 4 | Unit/native attributes, not yet fully split | Stable per actor; preserved in raw export |
| `0x06` | 1 | Record index linkage | Sequential values in serialized table |
| `0x07` | 1 | Side/object type | Active map-31 records are side 0 or 2 |
| `0x08` | 1 | Grid X | Active coordinates are in 0..19 |
| `0x09` | 1 | Grid Y | Active coordinates are in 0..31 |
| `0x0A..0x0D` | 4 | Target/animation fields, pending semantic split | `ff ff 00 00` in inactive records |
| `0x0E` | 1 | Status/class field | Active map-31 records all contain `0x02` |
| `0x0F..0x19` | 11 | Flags, animation and equipment fields | Retained verbatim for future native correlation |

Map 31 has 32 active actors: seven side-0 records at rows 4..9 and twenty-five side-2 records at rows 19..25. Inactive slots use `x=y=255`. The coordinate ranges and their separation match the 20x32 terrain buffer, confirming that offsets `0x08/0x09` are logical cells rather than screen pixels.
