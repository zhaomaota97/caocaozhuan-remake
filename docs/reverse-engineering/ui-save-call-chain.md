# UI Save Call Chain

The recovered function `0x41B16A(this, slot)` is the UI save handler. It formats the slot path/name from `slot`, asks the window object at `this+0x0C` for confirmation, then serializes the save payload:

1. Set save version byte to `5` and collect global mode/map/turn fields.
2. Serialize 128 fixed-size world objects through `0x42A766`.
3. Serialize 512 unit records through `0x408F2E` into the save buffer at offset `0x14DC`.
4. Write the main data partition with `0x41927D` and close it.
5. Write the slot's auxiliary partition through `0x417C84`/`0x41929A`, using the formatted slot name.
6. Refresh the save-list UI and return `1`; confirmation failure returns `0` without writing.

The native slot-8 load trace confirms the inverse UI path and required resources (`SV08D.E5S`, `SV08E.E5S`, `SV08S.E5S`, map/art resources), while recording `save_function_called=false` because it was a load-only run. Thus the serializer and UI loader are independently verified; a complete unmodified UI save-then-load round trip remains open until the save command itself is automated.

```powershell
python tools/verify_ui_save_chain.py
```

Current static command-chain gate: `dialog_dispatcher`, `load_branch`, `save_branch`, `save_command_101`, `load_command_102`, and `settings_command_107` all PASS. This verifies command routing and labels, not a completed UI save/load round trip. The latter remains deliberately open because the native confirmation path has not yet yielded a stable post-confirmation main-buffer read.
# Command-level dispatch

The dialog command dispatcher is `0x41AC86(this, command_id)`. It validates the command through the dialog vtable; when `this+0x26C == 0` it routes to load handler `0x41AD06`, and when nonzero it routes to save handler `0x41B16A(this, command_id)`. A successful handler result closes the dialog. Menu-state routine `0x4759BC` enables or disables save-related command IDs `0x6B`, `0x6D`, and `0x6E` according to battle/main-mode state. This provides the exact command-level path required for future UI automation, independent of toolbar icon order.

The inverse loader `0x41AD06(this, slot)` validates slot range `0..9`, reads the main partition, and requires version byte `5`. It then reads a fixed `0x56DC`-byte payload, restores the global fields, 128 object records, and 512 unit records through `0x409188`, and loads the auxiliary partition. Invalid/missing files, version `0`, or versions other than `5` return failure without committing state. After successful deserialization it sets runtime refresh flags (`DAT_004AAB94`, `DAT_0048B4C8`, and bit `8` in `DAT_004ABF9C`) and rebuilds dependent UI/battle state, proving that some runtime fields are reconstructed rather than serialized verbatim.
# Command Mapping Correction

The original APPMENU resource and TBBUTTON table at 0x48EA78 establish save=101, load=102, settings=107. Earlier statements naming 0x6B (107), 0x6D or 0x6E as save commands were not supported: their occurrence in a menu enable/disable routine does not prove save semantics. Those statements are superseded. `verify_ui_save_chain.py` now parses the original menu resource and validates actual labels rather than matching incidental constants. The observation harness posts WM_COMMAND 101 asynchronously; this alone is not proof of a completed UI save round trip.
