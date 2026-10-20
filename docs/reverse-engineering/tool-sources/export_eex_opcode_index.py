#!/usr/bin/env python3
"""Export a compact, reviewable EEX opcode/handler index from static catalog data."""
import csv, json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = json.loads((root / "analysis" / "eex-handlers.json").read_text(encoding="utf-8"))
rows = src if isinstance(src, list) else src.get("value", src.get("handlers", []))
out = root / "analysis" / "eex" / "opcode-index.csv"
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["opcode", "handler", "parameter_tags", "classification"])
    for row in rows:
        op = row.get("opcode")
        handler = row.get("handler") or ""
        tags = row.get("parameter_tag_calls_in_source_order", [])
        if not handler:
            cls = "reserved/terminal"
        elif 5 in tags:
            cls = "string-capable (tag 5 observed)"
        elif tags:
            cls = "parameterized"
        else:
            cls = "no parameter-reader call observed"
        w.writerow([op, handler, " ".join(map(str, tags)), cls])
print(f"wrote {out} ({len(rows)} opcodes)")
