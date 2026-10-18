# Native camera target field

## Recovered field

`FUN_00403360` is not a decoder. Its complete body is:

```c
int __fastcall FUN_00403360(int record) { return record + 6; }
```

The live actor table is at `0x004B2C50`, with a stride of `0x24` bytes. Therefore
the camera target bytes are:

| field | address | meaning |
|---|---:|---|
| X | `0x004B2C50 + slot*0x24 + 0x06` | actor/map tile X, unsigned byte |
| Y | `0x004B2C50 + slot*0x24 + 0x07` | actor/map tile Y, unsigned byte |

`0x405744` reads the `uint16` at `record+6`, splits low/high bytes, and passes
them to `0x455123`. `0x455123` then clamps the proposed camera tile against
the current camera and native map dimensions before calling the discrete
stepper `0x454CEF`. This is the source of the two-byte geometry value; it is
not an effect-shape or viewport rectangle.

## Reproduction

For a native actor snapshot, read each 36-byte record little-endian and use
`record[6]` and `record[7]`. The web port may use this field only when the
presentation caller has a verified actor slot. It must not replace the field
with generic screen-centering logic.

## Remaining uncertainty

The exact `param_3` slot passed by each presentation caller still needs to be
captured for every action type. The field layout and camera stepping algorithm
are established independently of that caller mapping.
