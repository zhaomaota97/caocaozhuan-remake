# Battle termination dispatch tail

The recovered tail of `FUN_0043AD1C` makes the next-state boundary explicit:

- it invokes `FUN_0043A956` and `FUN_00440252` after resolving the result;
- if actor flag `0x80` is clear and actor class is not `4`, it branches on
  `DAT_004B2C44`;
- `DAT_004B2C44 == 0xFF` calls `FUN_0043AAFB` (AI/automatic target path);
- otherwise it calls `FUN_00441488(..., type=2, DAT_004B2C28,
  DAT_004B2C44)`, then `FUN_0043DC99`;
- when `DAT_004B2C44 == 0x39`, it sets `_DAT_004B420C = 1`;
- a later flag/class predicate can call `FUN_00442718(param_1,2)`.

This is a concrete static end-of-action transition, including the `0x39`
special branch that writes the global termination candidate. It still does not
prove that `0x4B420C` means victory; a live end-state trace is required.
