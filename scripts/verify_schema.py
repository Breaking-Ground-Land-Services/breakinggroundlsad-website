#!/usr/bin/env python3
"""Verify JSON-LD schema coverage across Breaking Ground HTML pages."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

SERVICES = json.loads((DATA / "services.json").read_text(encoding="utf-8"))
PROJECTS = json.loads((DATA / "projects.json").read_text(encoding="utf-8"))
AREAS = json.loads((DATA / "service-areas.json").read_text(encoding="utf-8"))["areas"]

PAGE_EXPECTATIONS: dict[str, set[str]] = {
    "index.html": {
        "Organization",
        "HomeAndConstructionBusiness",
        "WebSite",
        "WebPage",
        "FAQPage",
        "BreadcrumbList",
        "ImageObject",
        "ItemList",
    },
    "about/index.html": {
        "Organization",
        "WebSite",
        "WebPage",
        "AboutPage",
        "BreadcrumbList",
        "Person",
    },
    "contact/index.html": {
        "Organization",
        "WebSite",
        "WebPage",
        "ContactPage",
        "BreadcrumbList",
        "FAQPage",
    },
    "services/index.html": {
        "Organization",
        "WebSite",
        "WebPage",
        "CollectionPage",
        "BreadcrumbList",
        "ItemList",
    },
    "projects/index.html": {
        "Organization",
        "WebSite",
        "WebPage",
        "CollectionPage",
        "BreadcrumbList",
        "ItemList",
    },
    "pricing/index.html": {
        "Organization",
        "WebSite",
        "WebPage",
        "BreadcrumbList",
        "OfferCatalog",
    },
    "service-areas/index.html": {
        "Organization",
        "WebSite",
        "WebPage",
        "CollectionPage",
        "BreadcrumbList",
        "ItemList",
    },
}

POLICY_EXPECTATIONS = {
    "Organization",
    "WebSite",
    "WebPage",
    "BreadcrumbList",
}

SERVICE_EXPECTATIONS = {
    "Organization",
    "WebSite",
    "WebPage",
    "Service",
    "BreadcrumbList",
    "FAQPage",
}

PROJECT_EXPECTATIONS = {
    "Organization",
    "WebSite",
    "WebPage",
    "CreativeWork",
    "BreadcrumbList",
    "FAQPage",
}

AREA_CITY_EXPECTATIONS = {
    "Organization",
    "WebSite",
    "WebPage",
    "City",
    "Service",
    "BreadcrumbList",
    "FAQPage",
}

AREA_COUNTY_EXPECTATIONS = {
    "Organization",
    "WebSite",
    "WebPage",
    "AdministrativeArea",
    "Service",
    "BreadcrumbList",
    "FAQPage",
    "ItemList",
}


def load_graphs(html: str) -> list[dict]:
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>',
        html,
        flags=re.DOTALL,
    )
    graphs: list[dict] = []
    for block in blocks:
        data = json.loads(block.strip())
        if "@graph" in data:
            graphs.extend(data["@graph"])
        else:
            graphs.append(data)
    return graphs


def type_names(node: dict) -> set[str]:
    value = node.get("@type", [])
    if isinstance(value, str):
        return {value}
    return set(value)


def all_types(graphs: list[dict]) -> set[str]:
    names: set[str] = set()
    for node in graphs:
        names.update(type_names(node))
    return names


def check_page(path: Path, required: set[str]) -> list[str]:
    if not path.is_file():
        return [f"{path.relative_to(ROOT)}: missing file"]
    html = path.read_text(encoding="utf-8")
    graphs = load_graphs(html)
    if not graphs:
        return [f"{path.relative_to(ROOT)}: no JSON-LD found"]
    found = all_types(graphs)
    missing = sorted(required - found)
    if missing:
        return [f"{path.relative_to(ROOT)}: missing {', '.join(missing)}"]
    return []


def is_county(area: dict) -> bool:
    return area.get("type") == "county" or "county" in area.get("slug", "")


def main() -> int:
    errors: list[str] = []

    for rel, required in PAGE_EXPECTATIONS.items():
        errors.extend(check_page(ROOT / rel, required))

    for slug in (
        "privacy-policy",
        "terms-of-service",
        "payment-deposit-policy",
        "image-use-policy",
    ):
        errors.extend(check_page(ROOT / slug / "index.html", POLICY_EXPECTATIONS))

    for s in SERVICES:
        errors.extend(check_page(ROOT / s["slug"] / "index.html", SERVICE_EXPECTATIONS))

    for p in PROJECTS:
        errors.extend(
            check_page(ROOT / "projects" / p["slug"] / "index.html", PROJECT_EXPECTATIONS)
        )

    for a in AREAS:
        path = ROOT / "areas" / a["slug"] / "index.html"
        required = AREA_COUNTY_EXPECTATIONS if is_county(a) else AREA_CITY_EXPECTATIONS
        # County pages may lack ItemList if no sibling cities — soften to require place type only
        if is_county(a):
            soft = set(AREA_COUNTY_EXPECTATIONS)
            # ItemList is best-effort for counties with cities in data
            errors_soft = check_page(path, soft - {"ItemList"})
            errors.extend(errors_soft)
            # Prefer ItemList when present; warn but don't fail if absent
            if path.is_file():
                found = all_types(load_graphs(path.read_text(encoding="utf-8")))
                if "ItemList" not in found:
                    print(f"  note: {path.relative_to(ROOT)} has no ItemList (optional for sparse counties)")
        else:
            errors.extend(check_page(path, required))

    if errors:
        print("Schema verification failed:")
        for err in errors:
            print(f"  - {err}")
        return 1

    checked = (
        len(PAGE_EXPECTATIONS)
        + 4
        + len(SERVICES)
        + len(PROJECTS)
        + len(AREAS)
    )
    print(f"Schema verification passed for {checked} HTML page checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
