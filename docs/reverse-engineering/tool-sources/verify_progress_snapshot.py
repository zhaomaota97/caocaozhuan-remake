"""Validate the machine-readable progress snapshot against current reports."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    snapshot = json.loads((ROOT / "analysis/progress-snapshot-20261018.json").read_text(encoding="utf-8"))
    gaps = json.loads((ROOT / "analysis/open-work-items.json").read_text(encoding="utf-8"))["items"]
    audit = json.loads((ROOT / "analysis/reverse-coverage-audit.json").read_text(encoding="utf-8"))
    if snapshot.get("completionClaim") is not False:
        raise SystemExit("completionClaim must remain false while open items exist")
    if snapshot.get("knownGapCount") != len(gaps) or len(gaps) != len(audit.get("knownGaps", [])):
        raise SystemExit("known gap counts disagree")
    if audit.get("completionClaim") is not False:
        raise SystemExit("audit completionClaim unexpectedly true")
    print(f"Progress snapshot: completionClaim=false, known gaps={len(gaps)}")


if __name__ == "__main__":
    main()
