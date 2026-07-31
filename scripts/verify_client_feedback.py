#!/usr/bin/env python3
from pathlib import Path

checks = {
    "demolition/index.html": ["IMG_8345-scaled", "guy-and-andrew-glasses", "Lot ready"],
    "mobile-home-demolition/index.html": ["IMG_8345-scaled", "guy-and-andrew-glasses"],
    "shed-barn-removal/index.html": ["Step 1", "Step 4", "Step 5"],
    "stump-removal/index.html": [
        "Why full stump removal beats grinding",
        "stump-grinding-companies",
        "carrying-a-stump-02",
    ],
    "tree-removal/index.html": ["dawns-job/before", "tree-removal-instance-a-03", "IMG_8145"],
    "storm-debris-cleanup/index.html": [
        "caroline-holt/before-01",
        "cutting-up-the-trees",
        "six-months-later",
    ],
    "pond-drainage/index.html": [
        "Why customers dig a pond",
        "a-berm-to-prevent-washouts",
        "removing-dirt-from-the-center",
    ],
    "grading-site-preparation/index.html": [
        "Builder-focused",
        "guy-and-andrew-glasses",
        "guy-and-andrew-equipment",
    ],
    "services/index.html": [
        "stump-removal-instance-a-01",
        "caroline-holt/before-01",
        "excavator-clearing-land",
    ],
    "about/index.html": ["guy-and-andrew-glasses"],
    "projects/bills-pond/index.html": [
        "Search topics this project answers",
        "excavator-on-a-pile-of-dirt",
        "installed-an-airator",
    ],
    "projects/caroline-holt/index.html": ["Storm Tree Cleanup", "Storm Cleanup"],
    "projects/dawns-job/index.html": [">Tree Removal<"],
    "projects/wanes-stump/index.html": ["5 tons", "youtube.com/shorts/iiDs5IUCmBM"],
    "projects/stump-removal-portfolio/index.html": ["grinding-vs-removal-comparison"],
    "projects/index.html": ["Storm Cleanup", "Tree Removal"],
    "header.html": ["Storm Cleanup", "Tree Removal"],
}

missing = 0
for path, needles in checks.items():
    text = Path(path).read_text(encoding="utf-8")
    print("==", path)
    for needle in needles:
        ok = needle in text
        print(" ", "OK" if ok else "MISSING", needle)
        if not ok:
            missing += 1

pond = Path("pond-drainage/index.html").read_text(encoding="utf-8")
print("pond service-shot count", pond.count('class="service-shot"'))
print("pond has before-vertical", "before-vertical" in pond)
bills = Path("projects/bills-pond/index.html").read_text(encoding="utf-8")
print("bills has before-vertical", "before-vertical" in bills)
print("missing total", missing)
