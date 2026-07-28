#!/usr/bin/env python3
"""Preview a broad set of project images to find demolition/shed/mobile-home shots."""
from __future__ import annotations

import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_img_preview" / "scan"
OUT.mkdir(parents=True, exist_ok=True)

# Prefer names that might be structure-related + dated job shots + random large files
priority_names = [
    "IMG_6857", "IMG_6873", "IMG_6876", "IMG_68781", "IMG_0071", "IMG_0792", "IMG_3-scaled",
    "IMG_8127", "IMG_8145", "IMG_8248", "IMG_8249", "IMG_8250", "IMG_8532", "IMG_8537",
    "IMG_8495", "IMG_8416", "IMG_8451", "IMG_9083", "IMG_9164", "IMG_0078",
    "20250405", "20250522", "20250611", "20250712", "20250728",
]

html_refs: set[str] = set()
for html in (ROOT / "projects").rglob("*.html"):
    text = html.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r"/assets/images/projects/([^\"'?]+)", text):
        html_refs.add(m.group(1))
for html in ROOT.glob("*-shed*/**/*.html"):
    text = html.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r"/assets/images/projects/([^\"'?]+)", text):
        html_refs.add(m.group(1))

print("html refs", len(html_refs))
for name in sorted(html_refs):
    if any(k in name.lower() for k in ("shed", "barn", "mobile", "demo", "803", "824", "685", "687")):
        print(" ", name)

proj = ROOT / "assets" / "images" / "projects"
picked: list[Path] = []
for p in sorted(proj.glob("*.jpg")):
    low = p.name.lower()
    if any(k.lower() in low for k in priority_names) or p.name in html_refs:
        picked.append(p)

# Add facebook-ish numeric dumps
for p in sorted(proj.glob("*.jpg")):
    if p.name[0].isdigit() and p not in picked:
        picked.append(p)

picked = picked[:60]
print("previewing", len(picked))
index = []
for i, p in enumerate(picked):
    im = Image.open(p).convert("RGB")
    im.thumbnail((640, 480))
    dest = OUT / f"{i:02d}_{p.stem[:40]}.jpg"
    im.save(dest, quality=78)
    index.append(f"{dest.name} <= {p.name} ({Image.open(p).size})")
(OUT / "index.txt").write_text("\n".join(index), encoding="utf-8")
print("wrote", OUT)
