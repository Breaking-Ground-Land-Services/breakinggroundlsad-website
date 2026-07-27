#!/usr/bin/env python3
"""Import Google Drive job webps into site assets and rebuild projects.json + Projects nav."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCOMING = ROOT / "_incoming" / "drive-jobs"
ASSETS = ROOT / "assets" / "images" / "projects"
DATA = ROOT / "data" / "projects.json"
HEADER = ROOT / "header.html"

# Drive folder slug -> project metadata (nav/public labels are job-type, not client names)
JOBS = [
    {
        "incoming": "bills-pond",
        "slug": "bills-pond",
        "navLabel": "Pond Excavation",
        "h1": "Pond Excavation & Berm Work",
        "title": "Pond Excavation Project | Breaking Ground",
        "meta": "Pond excavation, berm construction, drainage pipe, and aerator install by Breaking Ground Land Services and Demolition.",
        "city": "Central Florida",
        "service": "Pond & Drainage",
        "servicePath": "/pond-drainage/",
        "summary": "Excavated and shaped a new pond, built a berm to prevent washouts, installed drainage, and added an aerator to limit algae.",
        "challenge": "Empty-basin earthwork needed controlled slopes, spoil management, and drainage detailing before natural groundwater fill.",
        "legacyUrls": ["/how-to-dig-a-pond/", "/projects/pond-earthwork-support/"],
    },
    {
        "incoming": "caroline-holt",
        "slug": "caroline-holt",
        "navLabel": "Tree & Stump Clearing",
        "h1": "Tree & Stump Clearing",
        "title": "Tree & Stump Clearing Project | Breaking Ground",
        "meta": "Tree cutting, stump excavation, and site cleanup by Breaking Ground Land Services and Demolition.",
        "city": "Central Florida",
        "service": "Tree Removal",
        "servicePath": "/tree-removal/",
        "summary": "Cut and processed trees, dug out stumps, and left the property cleaned up — with a six-month follow-up look.",
        "challenge": "Mixed tree work and stump excavation required sequencing cut-down, stump removal, and haul-off without leaving the yard unfinished.",
        "legacyUrls": [],
    },
    {
        "incoming": "dawns-job",
        "slug": "dawns-job",
        "navLabel": "Tree Takedown",
        "h1": "Tree Takedown & Stump Dig-Out",
        "title": "Tree Takedown Project | Breaking Ground",
        "meta": "Full tree takedown, branch cleanup, stump excavation, and dump-truck haul-off by Breaking Ground.",
        "city": "Central Florida",
        "service": "Tree Removal",
        "servicePath": "/tree-removal/",
        "summary": "Took the tree down section by section, cleaned branches, excavated the stump, and hauled debris away.",
        "challenge": "Controlled limb and trunk cutting near the work zone before digging and loading a heavy stump.",
        "legacyUrls": ["/projects/lakeland-highlands-tree-removal/"],
    },
    {
        "incoming": "shawns-clearing-job",
        "slug": "shawns-clearing",
        "navLabel": "Residential Clearing",
        "h1": "Residential Land Clearing",
        "title": "Residential Land Clearing Project | Breaking Ground",
        "meta": "Equipment land clearing, log sorting, stump work, and follow-up growth photos by Breaking Ground.",
        "city": "Central Florida",
        "service": "Land Clearing",
        "servicePath": "/land-clearing/",
        "summary": "Cleared the lot with excavator and dump truck, sorted logs, preserved a magnolia, and documented recovery months later.",
        "challenge": "Balancing aggressive clearing with selective tree save and multi-trip haul-off of logs and stumps.",
        "legacyUrls": ["/brooksville-land-clearing/", "/projects/brooksville-land-clearing/"],
    },
    {
        "incoming": "stolte-land-clearing",
        "slug": "stolte-land-clearing",
        "navLabel": "Heavy Land Clearing",
        "h1": "Heavy Land Clearing",
        "title": "Heavy Land Clearing Project | Breaking Ground",
        "meta": "Large land clearing with tree takedown, log piles, stump grinding, and a clean finished site by Breaking Ground.",
        "city": "Central Florida",
        "service": "Land Clearing",
        "servicePath": "/land-clearing/",
        "summary": "Cut and removed trees across the property, staged logs and burn piles, ground stumps, and finished with a cleared site.",
        "challenge": "High tree density and large stump volume required staged cutting, grinding, and haul/burn planning.",
        "legacyUrls": [],
    },
    {
        "incoming": "stump-removal",
        "slug": "stump-removal-portfolio",
        "navLabel": "Stump Removal",
        "h1": "Stump Removal Projects",
        "title": "Stump Removal Projects | Breaking Ground",
        "meta": "Multiple stump excavation and haul-off examples — digging, carrying, cleaning dirt, and one-year comparisons.",
        "city": "Central Florida",
        "service": "Stump Removal",
        "servicePath": "/stump-removal/",
        "summary": "A set of completed stump removals showing excavation, haul-away, and how sites look after cleanup.",
        "challenge": "Varying stump sizes and root masses needed full excavation rather than surface grinding alone.",
        "legacyUrls": [
            "/8-16-2024-better-than-stump-grinding/",
            "/stump-removal-in-lakeland/",
            "/projects/lakeland-stump-excavation/",
        ],
    },
    {
        "incoming": "tree-removal",
        "slug": "tree-removal-portfolio",
        "navLabel": "Tree Removal",
        "h1": "Tree Removal Projects",
        "title": "Tree Removal Projects | Breaking Ground",
        "meta": "Multiple tree removal job instances showing staged takedown and cleanup by Breaking Ground.",
        "city": "Central Florida",
        "service": "Tree Removal",
        "servicePath": "/tree-removal/",
        "summary": "Documented tree removal across several job instances, from standing trees through cut and cleared work zones.",
        "challenge": "Each instance needed controlled cutting and cleanup suited to access and nearby structures.",
        "legacyUrls": [],
    },
    {
        "incoming": "wanes-stump",
        "slug": "wanes-stump",
        "navLabel": "Large Stump Excavation",
        "h1": "Large Stump Excavation",
        "title": "Large Stump Excavation Project | Breaking Ground",
        "meta": "Large stump dig-out, haul-away, and hole backfill by Breaking Ground Land Services and Demolition.",
        "city": "Central Florida",
        "service": "Stump Removal",
        "servicePath": "/stump-removal/",
        "summary": "Excavated a large stump, hauled it away, covered the hole, and documented the weight of material removed.",
        "challenge": "Oversized stump and root ball required deep digging, heavy lifting, and proper backfill.",
        "legacyUrls": [],
    },
]


# Manual captions when filename wording is wrong or incomplete.
CAPTION_OVERRIDES = {
    "guy-standing-infront-of-a-hill.webp": "Spoil Turned into a Sodded Play Hill for the Kids",
}


def caption_from_name(name: str) -> str:
    """Turn kebab-case filenames into readable process titles.

    Examples:
      defining-the-shape-of-the-pond.webp -> Defining the shape of the pond
      after-01-this is a pond.webp -> After: This is a pond
      process-01-guy-standing-in-the-bottom-of-a-pond.webp -> Guy standing in the bottom of a pond
    """
    override = CAPTION_OVERRIDES.get(Path(name).name.lower()) or CAPTION_OVERRIDES.get(name)
    if override:
        return override

    stem = Path(name).stem
    stem = stem.replace("_", "-").replace(" ", "-")
    stem = re.sub(r"-{2,}", "-", stem).strip("-").lower()

    stage = ""
    m = re.match(r"^(before|after|process)(?:-?\d{1,3})?(?:-(.+))?$", stem)
    if m:
        stage = m.group(1)
        rest = (m.group(2) or "").strip("-")
        # Plain before/after with no description
        if not rest or rest in {"vertical", "01", "02", "03", "04"}:
            label = stage.capitalize()
            if rest == "vertical":
                label = f"{label} (vertical)"
            return label
        stem = rest

    # Drop trailing angle numbers: pulling-the-slopes-01 -> pulling-the-slopes
    stem = re.sub(r"-\d{2,3}$", "", stem)

    # Portfolio instance keys: tree-removal-instance-a-01 -> Tree removal instance A
    inst = re.match(r"^(.+?-instance)-([a-z])(?:-\d{2,3})?$", stem)
    if inst:
        stem = f"{inst.group(1)}-{inst.group(2).upper()}"

    fixes = {
        "airator": "aerator",
        "infront": "in front",
        "in-front": "in front",
    }
    for bad, good in fixes.items():
        stem = stem.replace(bad, good)

    words = [w for w in stem.replace("-", " ").split() if w]
    if not words:
        return stage.capitalize() if stage else "Project photo"

    # Sentence case; keep short connector words lowercase after the first word
    small = {"a", "an", "the", "of", "to", "in", "on", "for", "and", "into", "from"}
    titled = []
    for i, w in enumerate(words):
        if i > 0 and w.lower() in small:
            titled.append(w.lower())
        else:
            titled.append(w[:1].upper() + w[1:])
    text = " ".join(titled)

    if stage == "before":
        return f"Before: {text}"
    if stage == "after":
        return f"After: {text}"
    return text


def series_key(name: str) -> str:
    """Collapse angle variants (foo-01, foo-02) into one series key."""
    stem = Path(name).stem.lower()
    return re.sub(r"-\d{2,3}$", "", stem)


def sort_key(name: str) -> tuple:
    n = name.lower()
    if n.startswith("before"):
        bucket = 0
    elif n.startswith("after"):
        bucket = 2
    else:
        bucket = 1
    return (bucket, n)


def pick_images(files: list[Path], limit: int = 14, per_series: int = 1) -> list[Path]:
    """Prefer before -> process -> after; collapse angle variants unless per_series > 1."""
    files = sorted(files, key=lambda p: sort_key(p.name))
    chosen: list[Path] = []
    series_counts: dict[str, int] = {}

    def add(path: Path, force: bool = False) -> None:
        if len(chosen) >= limit:
            return
        key = series_key(path.name)
        count = series_counts.get(key, 0)
        if not force and count >= per_series:
            return
        series_counts[key] = count + 1
        chosen.append(path)

    befores = [p for p in files if p.name.lower().startswith("before")]
    afters = [p for p in files if p.name.lower().startswith("after")]
    process = [p for p in files if p not in befores and p not in afters]

    for p in befores:
        add(p, force=sum(1 for c in chosen if c.name.lower().startswith("before")) < 3)
    for p in process:
        add(p)
    for p in afters:
        add(p, force=sum(1 for c in chosen if c.name.lower().startswith("after")) < 4)

    if not chosen and files:
        chosen = files[:limit]
    return chosen


def hero_image(files: list[Path]) -> Path:
    for prefer in ("after-01", "after", "before-01", "before"):
        for p in files:
            if Path(p.name).stem.lower().startswith(prefer):
                return p
    # Prefer landscape-ish filenames without vertical
    non_vert = [p for p in files if "vertical" not in p.name.lower()]
    return (non_vert or files)[0]


def collect_webps(src: Path) -> list[Path]:
    return sorted(src.rglob("*.webp"), key=lambda p: str(p.relative_to(src)).lower())


def update_header(projects: list[dict]) -> None:
    text = HEADER.read_text(encoding="utf-8")
    links = ['          <p class="nav-menu-label">Featured Projects</p>', '          <a href="/projects/" role="menuitem">All Projects</a>']
    for p in projects:
        label = (
            p["navLabel"]
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        links.append(f'          <a href="{p["path"]}" role="menuitem">{label}</a>')
    block = "\n".join(links)
    pattern = re.compile(
        r'(<div class="nav-dropdown-menu" role="menu">)\s*'
        r'<p class="nav-menu-label">Featured (?:Work|Projects)</p>.*?'
        r'(</div>\s*</div>\s*\n\s*<div class="nav-dropdown-wrap">)',
        re.S,
    )
    repl = r"\1\n" + block + r"\n        \2"
    new_text, n = pattern.subn(repl, text, count=1)
    if n != 1:
        raise SystemExit("Could not locate Projects dropdown in header.html")
    # Keep root-absolute; apply_base_to_chrome will prefix siteBase on rebuild
    HEADER.write_text(new_text, encoding="utf-8")
    print("updated header Projects nav")


def main() -> None:
    if not INCOMING.exists():
        raise SystemExit(f"Missing incoming folder: {INCOMING}")

    projects: list[dict] = []
    for job in JOBS:
        src = INCOMING / job["incoming"]
        if not src.exists():
            print("SKIP missing", src)
            continue
        files = collect_webps(src)
        if not files:
            print("SKIP empty", src)
            continue

        dest = ASSETS / job["slug"]
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)

        # Copy all webps (preserve nested relative names flattened with --)
        copied: list[Path] = []
        for f in files:
            rel = f.relative_to(src)
            flat = "-".join(rel.parts)
            out = dest / flat
            shutil.copy2(f, out)
            copied.append(out)

        picks = pick_images(
            copied,
            limit=14,
            per_series=2 if job["slug"] == "tree-removal-portfolio" else 1,
        )
        hero = hero_image(copied)
        # Ensure hero is first in gallery list
        gallery_paths = [hero] + [p for p in picks if p != hero]
        gallery_paths = gallery_paths[:14]

        web_base = f"/assets/images/projects/{job['slug']}"
        project = {
            "slug": job["slug"],
            "path": f"/projects/{job['slug']}/",
            "navLabel": job["navLabel"],
            "legacyUrls": job["legacyUrls"],
            "title": job["title"],
            "h1": job["h1"],
            "meta": job["meta"],
            "city": job["city"],
            "service": job["service"],
            "servicePath": job["servicePath"],
            "summary": job["summary"],
            "challenge": job["challenge"],
            "image": f"{web_base}/{hero.name}",
            "images": [f"{web_base}/{p.name}" for p in gallery_paths],
            "gallery": [
                {"src": f"{web_base}/{p.name}", "caption": caption_from_name(p.name)}
                for p in gallery_paths
            ],
        }
        projects.append(project)
        print(f"{job['slug']}: {len(copied)} webps, gallery {len(gallery_paths)}, hero {hero.name}")

    DATA.write_text(json.dumps(projects, indent=2) + "\n", encoding="utf-8")
    print("wrote", DATA.relative_to(ROOT))
    update_header(projects)


if __name__ == "__main__":
    main()
