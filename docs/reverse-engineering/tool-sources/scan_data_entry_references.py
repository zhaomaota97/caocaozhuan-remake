"""Scan all recovered pseudocode for literal DATA.E5 entry references."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PSEUDO = ROOT / "analysis" / "native-main" / "pseudocode"
OUT = ROOT / "analysis" / "data-entry-reference-scan.json"

CALL = re.compile(r"FUN_0041b51e\([^\n]*?[, ]([0-9]+|0x[0-9a-fA-F]+)[,)]")


def main() -> None:
    rows = []
    for path in sorted(PSEUDO.glob("*.c")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "DATA_E5" not in text and "FUN_0041b51e" not in text:
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            if "FUN_0041b51e" not in line:
                continue
            match = CALL.search(line)
            value = None
            if match:
                value = int(match.group(1), 0)
            rows.append({"file": str(path.relative_to(ROOT)), "line": line_number, "entry": value, "text": line.strip()})
    result = {
        "calls": rows,
        "literalEntries": sorted({row["entry"] for row in rows if row["entry"] is not None}),
        "entries6to9": [row for row in rows if row["entry"] in {6, 7, 8, 9}],
        "method": "all recovered native-main pseudocode files",
        "caveat": "Indirect entry expressions remain separate from literal scan results.",
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"calls": len(rows), "literalEntries": result["literalEntries"], "entries6to9": len(result["entries6to9"])}))


if __name__ == "__main__":
    main()
