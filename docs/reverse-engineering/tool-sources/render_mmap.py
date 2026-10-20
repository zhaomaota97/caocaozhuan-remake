"""Render one decoded 640x400 Mmap index plane with a decoded palette."""
from __future__ import annotations

import sys
from pathlib import Path
from PIL import Image


def main(index_path: str, palette_path: str, output: str) -> None:
    pixels = Path(index_path).read_bytes()
    palette = Path(palette_path).read_bytes()
    if len(pixels) != 640 * 400:
        raise SystemExit(f"expected 256000 map bytes, got {len(pixels)}")
    if len(palette) != 768:
        raise SystemExit(f"expected 768 palette bytes, got {len(palette)}")
    rgb = palette
    image = Image.frombytes("P", (640, 400), pixels)
    image.putpalette(rgb)
    image.save(output)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: render_mmap.py INDEX.BIN PALETTE.BIN OUTPUT.PNG")
    main(*sys.argv[1:])
