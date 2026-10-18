# Slot 8 Interface State

The battlefield title is decoded from Sv08d.e5s offset 0x1B as CP936 text, through the same source field copied to 0x4B0758 during native loading. The standalone runtime reads its exported Unicode title from slot-08.json.

Battle state serialization begins at file offset 35. Native 0x44F384 restores state bytes 2/3 directly. Function 0x449ECA calls 0x47631D with current-turn byte + 1 and turn-limit byte. Slot 8 stores 1 and 25, yielding the display 2/25. These are exported automatically rather than authored constants.

BGM track is independently decoded through the main-save config loader and verified playlist mapping. Unit rendering uses independent sprites; no native composite scene image is used as a replacement for the game scene.
