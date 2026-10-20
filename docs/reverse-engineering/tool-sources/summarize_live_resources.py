"""Summarize files, sounds and decoded resource indices from a live event log."""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    folder = (ROOT / Path(sys.argv[1])).resolve()
    events = []
    malformed = 0
    for line in (folder / "events.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            malformed += 1
    payloads = [item.get("payload", item) for item in events]
    files = sorted({item.get("path") for item in payloads if item.get("event") in {"CreateFileA", "LoadLibraryA"} and item.get("path")})
    sounds = Counter(Path(item["path"]).name.upper() for item in payloads if item.get("event") == "sndPlaySoundA" and item.get("path"))
    resources = defaultdict(set)
    for item in payloads:
        if item.get("event") == "resource-entry":
            resources[item.get("container") or "<unknown>"].add(item.get("index"))
    result = {
        "source": str((folder / "events.jsonl").relative_to(ROOT)),
        "malformedLinesSkipped": malformed,
        "fileEvents": len(files),
        "files": files,
        "sounds": dict(sorted(sounds.items())),
        "resourceContainers": {name: sorted(value) for name, value in sorted(resources.items())},
        "nativeEntries": Counter(hex(item.get("rva")) for item in payloads if item.get("event") == "native-entry"),
    }
    result["nativeEntries"] = dict(sorted(result["nativeEntries"].items()))
    out = folder / "live-resource-summary.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(files), "sounds": dict(sounds), "containers": len(resources), "nativeEntries": result["nativeEntries"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
