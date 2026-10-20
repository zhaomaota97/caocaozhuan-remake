"""Summarize actor-offset-0 native target-shape probe artifacts."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
OUT_JSON = ANALYSIS / "native-target-shape-probe-summary.json"
OUT_MD = ANALYSIS / "native-target-shape-probe-summary.md"


def main() -> None:
    rows = []
    for path in sorted(ANALYSIS.glob("native-target-candidates-limit-0-1x*-1.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        cases = data.get("cases", [])
        shapes = sorted({case.get("shape") for case in cases if case.get("shape") is not None})
        if len(shapes) != 1:
            continue
        matches = [row for row in data.get("rows", []) if row.get("match") is True]
        rows.append({
            "shape": shapes[0],
            "artifact": str(path.relative_to(ROOT)),
            "cases": len(cases),
            "rows": len(data.get("rows", [])),
            "matchedRows": len(matches),
            "allRowsMatch": len(matches) == len(data.get("rows", [])),
        })
    result = {
        "actorOffset": 0,
        "method": "native Frida target-list probe artifacts",
        "shapes": rows,
        "validatedShapes": [row["shape"] for row in rows if row["allRowsMatch"]],
        "partialShapes": [row["shape"] for row in rows if not row["allRowsMatch"]],
        "caveat": "A shape is listed only when an artifact returned; process-destroyed combinations remain unverified.",
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Native target-shape probe summary", "", "Actor offset `0`, using saved and alternate-zero health modes with both flags.", "", "| Shape | Cases | Rows | Matched | Result |", "|---:|---:|---:|---:|---|"]
    for row in rows:
        result_text = "validated" if row["allRowsMatch"] else "partial"
        lines.append(f"| {row['shape']} | {row['cases']} | {row['rows']} | {row['matchedRows']} | {result_text} |")
    lines += ["", result["caveat"]]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"validatedShapes": result["validatedShapes"], "partialShapes": result["partialShapes"]}))


if __name__ == "__main__":
    main()
