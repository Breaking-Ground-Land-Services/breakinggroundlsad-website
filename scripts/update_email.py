#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "contact@breakinggroundlsad.com"
NEW = "contact@breakinggroundlsad.com"

for path in ROOT.rglob("*"):
    if path.is_dir():
        continue
    if any(part in {".git", "node_modules", "__pycache__"} for part in path.parts):
        continue
    if path.suffix.lower() not in {".html", ".json", ".md", ".js", ".py", ".txt", ".xml"}:
        continue
    text = path.read_text(encoding="utf-8")
    if OLD not in text:
        continue
    path.write_text(text.replace(OLD, NEW), encoding="utf-8")
    print(f"updated {path.relative_to(ROOT)}")

site = __import__("json").loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
print("site.json email:", site["email"])
