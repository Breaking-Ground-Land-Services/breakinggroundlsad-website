#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_site

build_site.AREAS = json.loads((build_site.DATA / "service-areas.json").read_text(encoding="utf-8"))
print("areas with hero", sum(1 for a in build_site.AREAS["areas"] if a.get("heroImage")))
build_site.build_service_areas()

html = (ROOT / "areas" / "kathleen-fl" / "index.html").read_text(encoding="utf-8")
m = re.search(r'page-hero__media[\s\S]*?src="([^"]+)"', html)
print("kathleen hero src", m.group(1) if m else None)
tampa = (ROOT / "areas" / "tampa-fl" / "index.html").read_text(encoding="utf-8")
m2 = re.search(r'page-hero__media[\s\S]*?src="([^"]+)"', tampa)
print("tampa hero src", m2.group(1) if m2 else None)
