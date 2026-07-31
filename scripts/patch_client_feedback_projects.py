#!/usr/bin/env python3
"""Patch projects.json with client-requested composite frames and metadata."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "data" / "projects.json"
projects = json.loads(path.read_text(encoding="utf-8"))

FRAMES = {
    "bills-pond": {
        "before": ["before.webp"],
        "process": [
            "removing-dirt-from-the-center-01.webp",
            "piling-the-dirt-into-a-mountain.webp",
            "pond-while-still-empty.webp",
            "pond-before-final-berm.webp",
        ],
        "after": ["after-01-this is a pond.webp"],
    },
    "caroline-holt": {
        "before": ["before-01.webp", "before-02.webp", "before-03.webp"],
        "process": ["cutting-up-the-trees.webp"],
        "after": ["after-01.webp", "after-02.webp", "six-months-later.webp"],
    },
    "dawns-job": {
        "before": ["before.webp"],
        "process": [
            "cutting-off-branches-01.webp",
            "cutting-down-the-trunk-of-the-tree-01.webp",
            "digging-out-the-stump-01.webp",
            "loading-a-stump-into-the-dump-truck-01.webp",
        ],
        "after": ["after.webp", "tree-is-now-a-stump.webp", "stumps-in-the-dump-truck.webp"],
    },
    "shawns-clearing": {
        "before": ["before.webp"],
        "process": [
            "excavator-clearing-land-01.webp",
            "piling-up-logs.webp",
            "sorting-through-logs.webp",
            "cleaning-up-01.webp",
        ],
        "after": ["after-01.webp"],
    },
    "stolte-land-clearing": {
        "before": ["before-01.webp", "before-02.webp", "before-03.webp"],
        "process": [
            "removing-the-trees-01.webp",
            "all-of-the-trees-cut-down-01.webp",
            "pile-of-logs-01.webp",
            "pile-of-stumps-to-burn-01.webp",
        ],
        "after": ["after-12.webp"],
    },
    "stump-removal-portfolio": {
        "before": [
            "stump-removal-instance-a-01.webp",
            "stump-removal-instance-b-01.webp",
            "stump-removal-instance-c-01.webp",
            "stump-removal-instance-d-01.webp",
        ],
        "process": [
            "stump-removal-instance-a-02.webp",
            "stump-removal-instance-b-02.webp",
            "carrying-a-stump-02.webp",
            "hauling-away-a-stump-03.webp",
        ],
        "after": [
            "after-01.webp",
            "after-04.webp",
            "stump-removal-instance-b-03.webp",
            "stump-removal-instance-a-04.webp",
        ],
    },
    "wanes-stump": {
        "before": ["before.webp"],
        "process": [
            "digging-out-the-stump-01.webp",
            "man-next-to-the-stump.webp",
            "pulling-the-stump-out-of-the-hole.webp",
            "stump-is-out.webp",
        ],
        "after": ["loading-the-stump.webp", "weight-of-what-we-hauled-away.webp"],
    },
}

for p in projects:
    slug = p["slug"]
    if slug in FRAMES:
        p["compositeFrames"] = FRAMES[slug]

    if slug == "caroline-holt":
        p["navLabel"] = "Storm Cleanup"
        p["title"] = "Storm Tree Cleanup Project | Breaking Ground"
        p["h1"] = "Storm Tree Cleanup"
        p["meta"] = (
            "Storm-fallen tree cutting, stump excavation, and property cleanup by "
            "Breaking Ground Land Services and Demolition."
        )
        p["service"] = "Storm Cleanup"
        p["servicePath"] = "/storm-debris-cleanup/"
        p["summary"] = (
            "Cut and processed storm-damaged trees, dug out stumps, and left the "
            "property cleaned up — with a six-month follow-up look."
        )
        p["challenge"] = (
            "Storm debris and mixed tree work required sequenced cutting, stump "
            "removal, and haul-off without leaving the yard unfinished."
        )
        ordered = [
            ("before-01.webp", "Before — storm damage"),
            ("before-02.webp", "Before — fallen timber"),
            ("before-03.webp", "Before — yard obstruction"),
            ("before-04.webp", "Before — work zone"),
            ("cutting-up-the-trees.webp", "Cutting up the trees"),
            ("digging-out-the-stumps.webp", "Digging out the stumps"),
            ("after-01.webp", "After"),
            ("after-02.webp", "After"),
            ("after-03.webp", "After"),
            ("six-months-later.webp", "Six months later"),
        ]
        p["gallery"] = [
            {"src": f"/assets/images/projects/caroline-holt/{name}", "caption": cap}
            for name, cap in ordered
        ]
        p["images"] = [g["src"] for g in p["gallery"]]

    if slug == "dawns-job":
        p["navLabel"] = "Tree Removal"
        p["title"] = "Tree Removal Project | Breaking Ground"
        p["h1"] = "Tree Removal"
        p["meta"] = (
            "Full tree takedown, branch cleanup, stump excavation, and dump-truck "
            "haul-off by Breaking Ground."
        )
        p["service"] = "Tree Removal"
        p["servicePath"] = "/tree-removal/"
        p["summary"] = (
            "Took the tree down section by section, cleaned branches, excavated "
            "the stump, and hauled debris away."
        )

    if slug == "bills-pond":
        ordered = [
            ("before.webp", "Before"),
            ("defining-the-shape-of-the-pond.webp", "Defining the Shape of the Pond"),
            ("removing-dirt-from-the-center-01.webp", "Removing Dirt from the Center"),
            ("piling-the-dirt-into-a-mountain.webp", "Piling the Dirt into a Mountain"),
            ("excavator-on-a-pile-of-dirt.webp", "Excavator on a Pile of Dirt"),
            ("pulling-the-slopes-01.webp", "Pulling the Slopes"),
            ("pond-while-still-empty.webp", "Pond While Still Empty"),
            ("pipe-to-allow-drainage.webp", "Pipe to Allow Drainage"),
            ("pond-before-final-berm.webp", "Pond Before Final Berm"),
            ("installed-an-airator-to-prevent-algae.webp", "Installed an Aerator to Prevent Algae"),
            ("guy-standing-infront-of-a-hill.webp", "Spoil Turned into a Sodded Play Hill for the Kids"),
            ("after-01-this is a pond.webp", "After: This Is a Pond"),
            ("the-pond-draws-water-from-the-ground-01.webp", "The Pond Draws Water from the Ground"),
            ("a-berm-to-prevent-washouts.webp", "A Berm to Prevent Washouts"),
        ]
        p["gallery"] = [
            {"src": f"/assets/images/projects/bills-pond/{name}", "caption": cap}
            for name, cap in ordered
        ]
        p["images"] = [g["src"] for g in p["gallery"]]

    if slug == "stump-removal-portfolio":
        ordered = [
            ("stump-removal-instance-a-01.webp", "Stump Removal Instance A — Before"),
            ("stump-removal-instance-b-01.webp", "Stump Removal Instance B — Before"),
            ("stump-removal-instance-c-01.webp", "Stump Removal Instance C — Before"),
            ("stump-removal-instance-d-01.webp", "Stump Removal Instance D — Before"),
            ("stump-removal-instance-a-02.webp", "Stump Removal Instance A — Process"),
            ("stump-removal-instance-b-02.webp", "Stump Removal Instance B — Process"),
            ("carrying-a-stump-02.webp", "Carrying a Stump"),
            ("hauling-away-a-stump-03.webp", "Hauling Away a Stump"),
            ("after-01.webp", "After"),
            ("after-04.webp", "After"),
            ("stump-removal-instance-b-03.webp", "Stump Removal Instance B — After"),
            ("stump-removal-instance-a-04.webp", "Stump Removal Instance A — After"),
            ("cleaning-the-dirt-out-of-a-stump.webp", "Cleaning the Dirt Out of a Stump"),
            ("guy-next-to-a-stump-01.webp", "Guy Next to a Stump"),
        ]
        p["gallery"] = [
            {"src": f"/assets/images/projects/stump-removal-portfolio/{name}", "caption": cap}
            for name, cap in ordered
        ]
        p["images"] = [g["src"] for g in p["gallery"]]
        p["comparisonComposite"] = (
            "/assets/images/projects/stump-removal-portfolio/grinding-vs-removal-comparison.webp"
        )

    if slug == "wanes-stump":
        ordered = [
            ("before.webp", "Before"),
            ("32-inch-chainsaw-for-reference.webp", "32 Inch Chainsaw for Reference"),
            ("digging-out-the-stump-01.webp", "Digging Out the Stump"),
            ("man-next-to-the-stump.webp", "Man Next to the Stump"),
            ("pulling-the-stump-out-of-the-hole.webp", "Pulling the Stump Out of the Hole"),
            ("stump-is-out.webp", "Stump Is Out"),
            ("loading-the-stump.webp", "Loading the Stump"),
            ("weight-of-what-we-hauled-away.webp", "Weight of What We Hauled Away"),
            ("hauling-the-stump-away.webp", "Hauling the Stump Away"),
            ("covering-up-the-hole.webp", "Covering Up the Hole"),
        ]
        p["gallery"] = [
            {"src": f"/assets/images/projects/wanes-stump/{name}", "caption": cap}
            for name, cap in ordered
        ]
        p["images"] = [g["src"] for g in p["gallery"]]
        p["youtubeUrl"] = "https://youtube.com/shorts/iiDs5IUCmBM?feature=share"
        p["youtubeLabel"] = "Watch us remove this stump on YouTube"

path.write_text(json.dumps(projects, indent=2) + "\n", encoding="utf-8")
print("projects.json patched", len(projects))
for p in projects:
    if p.get("compositeFrames"):
        print(p["slug"], {k: len(v) for k, v in p["compositeFrames"].items()})
