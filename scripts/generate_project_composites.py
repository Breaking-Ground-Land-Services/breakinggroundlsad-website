#!/usr/bin/env python3
"""Stage Breaking Ground project photos and build branded before/process/after composites."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
COMPOSITE_SCRIPT = ROOT / "scripts" / "build-before-process-after-composite.py"
STAGING_ROOT = ROOT / "_incoming" / "composite-staging"
OUT_ROOT = ROOT / "assets" / "images" / "projects"


def classify(name: str) -> str | None:
    stem = Path(name).stem.lower().replace(" ", "-")
    if stem.startswith("before") or stem in {"man-next-to-the-stump", "guy-next-to-a-stump-01", "guy-next-to-a-stump-02"}:
        return "before"
    if stem.startswith("after") or "months-later" in stem or "one-year-later" in stem or stem in {
        "stump-is-out",
        "covering-up-the-hole",
        "weight-of-what-we-hauled-away",
        "six-months-later",
        "three-months-later",
    }:
        return "after"
    if stem.startswith("process"):
        return "process"
    # Instance portfolios: first shot before-ish, last after-ish handled in stage_portfolio
    if "instance" in stem:
        return None
    return "process"


def pick(files: list[Path], kind: str, limit: int) -> list[Path]:
    matched = [p for p in files if classify(p.name) == kind]
    return matched[:limit]


def stage_standard(src: Path, staging: Path) -> dict[str, int]:
    files = sorted(src.glob("*.webp"), key=lambda p: p.name.lower())
    counts = {"before": 0, "process": 0, "after": 0}
    buckets = {
        "before": pick(files, "before", 3),
        "after": pick(files, "after", 3),
        "process": pick(files, "process", 4),
    }
    # Fallback if a phase is empty
    unused = [p for p in files if p not in buckets["before"] + buckets["process"] + buckets["after"]]
    if not buckets["before"] and unused:
        buckets["before"] = [unused.pop(0)]
    if not buckets["after"] and unused:
        buckets["after"] = [unused.pop()]
    if not buckets["process"]:
        buckets["process"] = unused[:4]

    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    for kind, paths in buckets.items():
        for i, path in enumerate(paths, start=1):
            dest = staging / f"{kind}-{i:02d}{path.suffix.lower()}"
            shutil.copy2(path, dest)
            counts[kind] += 1
    return counts


def stage_portfolio(src: Path, staging: Path) -> dict[str, int]:
    """tree-removal-instance-* style: treat first of each instance as before, mid process, last after."""
    files = sorted(src.glob("*.webp"), key=lambda p: p.name.lower())
    groups: dict[str, list[Path]] = {}
    for path in files:
        m = re.match(r"(.+-instance-[a-z])-\d+", path.stem.lower())
        key = m.group(1) if m else "misc"
        groups.setdefault(key, []).append(path)

    befores, process, afters = [], [], []
    for items in groups.values():
        if not items:
            continue
        befores.append(items[0])
        if len(items) > 2:
            process.extend(items[1:-1][:2])
        if len(items) > 1:
            afters.append(items[-1])

    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    counts = {"before": 0, "process": 0, "after": 0}
    for kind, paths in (("before", befores[:3]), ("process", process[:4]), ("after", afters[:3])):
        for i, path in enumerate(paths, start=1):
            shutil.copy2(path, staging / f"{kind}-{i:02d}{path.suffix.lower()}")
            counts[kind] += 1
    return counts


def build_one(project: dict) -> dict:
    slug = project["slug"]
    src = OUT_ROOT / slug
    if not src.is_dir():
        return {"slug": slug, "status": "missing-source"}

    staging = STAGING_ROOT / slug
    if any("instance-" in p.name for p in src.glob("*.webp")):
        counts = stage_portfolio(src, staging)
    else:
        counts = stage_standard(src, staging)

    if counts["before"] < 1 or counts["after"] < 1:
        return {"slug": slug, "status": "insufficient", "counts": counts}

    basename = f"before-process-after-{slug}"
    out_dir = src
    title = project.get("navLabel") or project["h1"]
    cmd = [
        sys.executable,
        str(COMPOSITE_SCRIPT),
        str(staging),
        "--title",
        title,
        "--basename",
        basename,
        "--out",
        str(out_dir),
        "--also-jpeg",
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if proc.returncode != 0:
        return {
            "slug": slug,
            "status": "error",
            "stderr": (proc.stderr or proc.stdout)[-800:],
            "counts": counts,
        }

    webp = out_dir / f"{basename}.webp"
    return {
        "slug": slug,
        "status": "built",
        "counts": counts,
        "composite": f"/assets/images/projects/{slug}/{basename}.webp",
        "compositeExists": webp.is_file(),
    }


def main() -> int:
    results = []
    for project in PROJECTS:
        result = build_one(project)
        results.append(result)
        print(result["slug"], result["status"], result.get("counts"), result.get("composite", ""))
        if result["status"] == "error":
            print(result.get("stderr", ""))

    # Patch projects.json with composite fields
    by_slug = {r["slug"]: r for r in results if r.get("status") == "built"}
    updated = []
    for project in PROJECTS:
        item = dict(project)
        built = by_slug.get(project["slug"])
        if built:
            item["composite"] = built["composite"]
            item["compositeCaption"] = (
                f"Before / process / after composite for {project['navLabel']} — "
                f"numbered frames pair with the story sections below. "
                f"Call {json.loads((ROOT / 'data' / 'site.json').read_text(encoding='utf-8'))['phone']} for a similar estimate."
            )
            # Prefer composite as card/hero image
            item["image"] = built["composite"]
        updated.append(item)
    (ROOT / "data" / "projects.json").write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
    print("updated projects.json composites")
    return 0 if all(r["status"] == "built" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
