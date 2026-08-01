#!/usr/bin/env python3
"""Point /assets/ image refs in data/*.json at .webp counterparts."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ASSET_RE = re.compile(r"^/assets/.+\.(jpe?g|png)$", re.I)


def migrate_str(value: str) -> str:
    if ASSET_RE.match(value):
        return re.sub(r"\.(jpe?g|png)$", ".webp", value, flags=re.I)
    return value


def migrate_obj(obj):
    if isinstance(obj, dict):
        return {k: migrate_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [migrate_obj(v) for v in obj]
    if isinstance(obj, str):
        return migrate_str(obj)
    return obj


def main() -> int:
    for path in sorted(DATA.glob("*.json")):
        if path.name == "image-manifest.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        migrated = migrate_obj(data)
        if migrated != data:
            path.write_text(json.dumps(migrated, indent=2) + "\n", encoding="utf-8")
            print("updated", path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
