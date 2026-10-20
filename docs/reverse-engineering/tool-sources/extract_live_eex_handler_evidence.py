"""Convert a live observer event stream into opcode evidence for the matrix."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "analysis" / "live-startup-20261018-043631" / "events.jsonl"
OUT = ROOT / "analysis" / "native-eex-live-new-game-validation.json"


def main() -> None:
    source = (ROOT / Path(__import__("sys").argv[1])).resolve() if len(__import__("sys").argv) > 1 else DEFAULT
    events = []
    for line in source.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        payload = item.get("payload", item)
        if payload.get("event") == "eex-handler":
            events.append({
                "opcode": payload.get("opcode"),
                "handler_rva": payload.get("handler_rva"),
                "cursor_field": payload.get("cursor_field"),
                "source_event": str(source.relative_to(ROOT)),
            })
    unique = {(row["opcode"], row["handler_rva"]): row for row in events}
    result = {
        "source": str(source.relative_to(ROOT)),
        "method": "live observe_live_game eex-handler hook",
        "events": list(unique.values()),
        "opcodes": sorted({row["opcode"] for row in unique.values()}),
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"live EEX handlers: {len(result['events'])} events, opcodes={result['opcodes']}")


if __name__ == "__main__":
    main()
