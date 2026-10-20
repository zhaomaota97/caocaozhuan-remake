#!/usr/bin/env python3
"""Extract direct call edges from Rizin's analyzed PE functions."""
import json, subprocess, csv
from pathlib import Path

root = Path(__file__).resolve().parents[1]
rizin = r"C:\Program Files\Rizin\bin\rizin.exe"
dlls = sorted(root.glob("*.dll"))
out = root / "analysis" / "dll-calls.csv"
edges = []
for dll in dlls:
    cmd = [rizin, "-q", "-c", "aaa", "-c", "aflj", str(dll)]
    p = subprocess.run(cmd, capture_output=True, text=True, check=True)
    funcs = json.loads(p.stdout or "[]")
    for fn in funcs:
        addr = fn.get("offset")
        for ref in fn.get("callrefs", []):
            if ref.get("type") == "CALL" and ref.get("to") is not None:
                edges.append((dll.name, f"0x{addr:x}", f"0x{ref['to']:x}"))
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["dll", "caller", "callee"]); w.writerows(edges)
print(f"wrote {out} ({len(edges)} direct internal/absolute call edges)")
