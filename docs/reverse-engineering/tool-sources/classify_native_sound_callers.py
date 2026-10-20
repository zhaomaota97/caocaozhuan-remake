"""Classify native sound wrapper callers using evidence-backed roles."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "analysis" / "native-ui-sound-calls.json"
OUTPUT = ROOT / "analysis" / "native-ui-sound-caller-roles.json"

ROLE_CALLERS = {
    "turn-transition": {"004337f4", "00433bc8"},
    "movement-animation": {"0043d538"},
    "ai-target-selection": {"0043dada", "0043aafb"},
    "target-selection": {"0045533d"},
    "combat-result": {"004404bd"},
    "combat-loop": {"004064f1"},
    "effect-or-battle": {"00441744", "0041c762"},
}


def classify(caller: str) -> str:
    for role, callers in ROLE_CALLERS.items():
        if caller.lower() in callers:
            return role
    return "unclassified"


def main() -> None:
    source = json.loads(INPUT.read_text(encoding="utf-8"))
    grouped = defaultdict(list)
    for call in source.get("calls", []):
        item = dict(call)
        item["role"] = classify(str(call.get("caller", "")))
        grouped[item["role"]].append(item)
    result = {
        "source": str(INPUT.relative_to(ROOT)),
        "wrapper": source.get("wrapper"),
        "method": "static caller-role classification; unknown callers retained",
        "roles": {key: grouped[key] for key in sorted(grouped)},
        "roleCounts": {key: len(grouped[key]) for key in sorted(grouped)},
        "caveat": "Roles describe call-site context only; select/cancel sound IDs require dynamic UI evidence.",
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["roleCounts"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
