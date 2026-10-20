"""Validate the machine-readable open-work evidence matrix."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "analysis" / "open-work-items.json"


def main() -> None:
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    rows = data.get("items", [])
    expected = {
        "eex-full-playthrough", "dll-business-semantics", "ui-driven-battle-input",
        "full-ai-turn-and-victory", "data-e5-entries-6-9", "ui-save-load-roundtrip",
        "later-actor-target-shapes",
    }
    actual = {row.get("id") for row in rows}
    if actual != expected or any(row.get("status") != "open" for row in rows):
        raise SystemExit("open-work item IDs/status mismatch")
    missing = []
    for row in rows:
        for evidence in row.get("evidence", []):
            if not (ROOT / evidence).exists():
                missing.append(evidence)
        if not row.get("boundary"):
            raise SystemExit(f"missing boundary: {row.get('id')}")
    if missing:
        raise SystemExit("missing evidence: " + ", ".join(missing))
    print(f"Open-work evidence matrix: {len(rows)}/{len(expected)} items and evidence paths valid")


if __name__ == "__main__":
    main()
