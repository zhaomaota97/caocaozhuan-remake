"""Summarize all native target-candidate probe artifacts by actor/shape context."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
OUT = ANALYSIS / "native-target-shape-matrix.json"

PATTERN = re.compile(r"native-target-candidates-limit-(\d+)-(\d+)x(\d+)(?:-\d+)?\.json$")


def main() -> None:
    contexts = []
    for path in sorted(ANALYSIS.glob("native-target-candidates-limit-*.json")):
        match = PATTERN.match(path.name)
        if not match:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows = data.get("rows", [])
        matched = sum(row.get("match") is True for row in rows)
        actor_values = sorted({case.get("slot") for case in data.get("cases", [])})
        shapes = sorted({case.get("shape") for case in data.get("cases", [])})
        contexts.append({
            "actorOffset": int(match.group(1)),
            "actorLimit": int(match.group(2)),
            "shapeOffset": int(match.group(3)),
            "actors": actor_values,
            "shapes": shapes,
            "rows": len(rows),
            "matched": matched,
            "allMatch": matched == len(rows),
            "artifact": str(path.relative_to(ROOT)),
        })
    result = {
        "artifacts": len(contexts),
        "contexts": contexts,
        "totalRows": sum(row["rows"] for row in contexts),
        "matchedRows": sum(row["matched"] for row in contexts),
        "caveat": "Missing artifacts represent native script destruction or an unrun context; they are not treated as matches.",
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"artifacts": result["artifacts"], "totalRows": result["totalRows"], "matchedRows": result["matchedRows"]}))


if __name__ == "__main__":
    main()
