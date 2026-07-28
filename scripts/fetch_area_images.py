#!/usr/bin/env python3
"""Download representative Wikimedia/Wikipedia images for each service area."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_DIR = ROOT / "assets" / "images" / "areas"
AREAS_PATH = DATA / "service-areas.json"
MANIFEST_PATH = DATA / "area-images.json"
UA = "BreakingGroundSiteBuilder/1.0 (https://breakinggroundlsad.com; contact@breakinggroundlsad.com)"

# Prefer these Wikipedia titles when the auto "{Name}, Florida" page is weak/missing.
TITLE_OVERRIDES = {
    "kathleen-fl": "Kathleen, Florida",
    "st-petersburg-fl": "St. Petersburg, Florida",
    "the-villages-fl": "The Villages, Florida",
    "fort-myers-fl": "Fort Myers, Florida",
    "fort-meade-fl": "Fort Meade, Florida",
    "cape-coral-fl": "Cape Coral, Florida",
    "daytona-beach-fl": "Daytona Beach, Florida",
    "winter-haven-fl": "Winter Haven, Florida",
    "lake-wales-fl": "Lake Wales, Florida",
    "dade-city-fl": "Dade City, Florida",
    "haines-city-fl": "Haines City, Florida",
    "polk-city-fl": "Polk City, Florida",
    "plant-city-fl": "Plant City, Florida",
    "polk-county-fl": "Polk County, Florida",
    "hernando-county-fl": "Hernando County, Florida",
    "hillsborough-county-fl": "Hillsborough County, Florida",
    "pasco-county-fl": "Pasco County, Florida",
    "orange-county-fl": "Orange County, Florida",
    "osceola-county-fl": "Osceola County, Florida",
    "lake-county-fl": "Lake County, Florida",
    "manatee-county-fl": "Manatee County, Florida",
    "lee-county-fl": "Lee County, Florida",
    "marion-county-fl": "Marion County, Florida",
    "alachua-county-fl": "Alachua County, Florida",
    "duval-county-fl": "Duval County, Florida",
}

# Known strong Commons/Wikipedia files when page lead image is a seal/map/logo.
FILE_OVERRIDES = {
    # Prefer scenic/downtown photos over seals/flags/maps.
    "lakeland-fl": "File:Downtownlakeland fl.JPG",
    "tampa-fl": "File:Tampa Skyline.jpg",
    "orlando-fl": "File:Orlando downtown.jpg",
    "jacksonville-fl": "File:Jacksonville Skyline 2020.jpg",
    "st-petersburg-fl": "File:St Petersburg FL skyline.jpg",
    "clearwater-fl": "File:Clearwater Beach Florida.jpg",
    "sarasota-fl": "File:Sarasota skyline.jpg",
    "fort-myers-fl": "File:Downtown Fort Myers.jpg",
    "naples-fl": "File:Naples Pier Florida.jpg",
    "daytona-beach-fl": "File:Daytona Beach Boardwalk and Pier.jpg",
    "ocala-fl": "File:Marion County Courthouse, Ocala, Florida.jpg",
    "gainesville-fl": "File:Downtown Gainesville Florida.jpg",
    "kissimmee-fl": "File:Kissimmee Florida downtown.jpg",
    "bradenton-fl": "File:Bradenton Florida riverside.jpg",
    "cape-coral-fl": "File:Cape Coral Yacht Club Beach.jpg",
    "melbourne-fl": "File:Melbourne Florida downtown.jpg",
    "clermont-fl": "File:Clermont Florida downtown.jpg",
    "brooksville-fl": "File:Hernando County Courthouse.jpg",
    "bartow-fl": "File:Polk County Courthouse Bartow Florida.jpg",
    "winter-haven-fl": "File:Winter Haven Florida downtown.jpg",
    "plant-city-fl": "File:Plant City Florida downtown.jpg",
    "lake-wales-fl": "File:Bok Tower Gardens Lake Wales Florida.jpg",
    "sebring-fl": "File:Highlands County Courthouse Sebring Florida.jpg",
    "the-villages-fl": "File:The Villages Florida downtown Spanish Springs.jpg",
}


def api_get(params: dict) -> dict:
    q = urllib.parse.urlencode(params)
    url = f"https://en.wikipedia.org/w/api.php?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.load(resp)


def commons_file_url(file_title: str) -> tuple[str | None, str | None]:
    """Resolve a File: title to original image URL + license hint."""
    title = file_title if file_title.startswith("File:") else f"File:{file_title}"
    data = api_get(
        {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|size|mime",
            "iiurlwidth": 1920,
            "redirects": 1,
        }
    )
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        meta = info.get("extmetadata") or {}
        license_short = (meta.get("LicenseShortName") or {}).get("value", "")
        url = info.get("thumburl") or info.get("url")
        return url, license_short
    return None, None


def page_image(title: str) -> tuple[str | None, str | None, str | None]:
    data = api_get(
        {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "pageimages|images",
            "piprop": "original|name",
            "pithumbsize": 1600,
            "imlimit": 20,
            "redirects": 1,
        }
    )
    pages = data.get("query", {}).get("pages", {})
    for pid, page in pages.items():
        if int(pid) < 0:
            return None, None, None
        resolved = page.get("title")
        file_name = page.get("pageimage")
        orig = (page.get("original") or {}).get("source")
        if file_name:
            url, lic = commons_file_url(f"File:{file_name}")
            if url:
                return url, lic, resolved
        if orig:
            return orig, "", resolved
    return None, None, None


def commons_search(query: str) -> tuple[str | None, str | None]:
    data = api_get(
        {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,  # File
            "gsrlimit": 8,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|mime|size",
            "iiurlwidth": 1920,
        }
    )
    pages = data.get("query", {}).get("pages", {})
    scored: list[tuple[int, str, str]] = []
    for page in pages.values():
        title = page.get("title") or ""
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        mime = (info.get("mime") or "").lower()
        if not mime.startswith("image/"):
            continue
        if mime in {"image/svg+xml", "image/gif"}:
            continue
        meta = info.get("extmetadata") or {}
        lic = (meta.get("LicenseShortName") or {}).get("value", "")
        # Skip clearly non-scenic assets.
        low = title.lower()
        if any(bad in low for bad in ("seal", "logo", "flag", "map of", "locator", "coat of arms", "svg")):
            continue
        url = info.get("thumburl") or info.get("url")
        if not url:
            continue
        w = int(info.get("width") or 0)
        score = w
        if any(k in low for k in ("downtown", "skyline", "courthouse", "beach", "pier", "lake", "main street")):
            score += 5000
        scored.append((score, url, lic))
    if not scored:
        return None, None
    scored.sort(reverse=True)
    return scored[0][1], scored[0][2]


def wiki_title_for(area: dict) -> str:
    slug = area["slug"]
    if slug in TITLE_OVERRIDES:
        return TITLE_OVERRIDES[slug]
    return f"{area['shortName']}, Florida"


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as resp:
        dest.write_bytes(resp.read())


def to_webp(src: Path, dest: Path, max_w: int = 1800) -> None:
    with Image.open(src) as im:
        im = im.convert("RGB")
        w, h = im.size
        if w > max_w:
            nh = int(h * (max_w / w))
            im = im.resize((max_w, nh), Image.Resampling.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        im.save(dest, "WEBP", quality=82, method=6)


def resolve_image(area: dict) -> dict:
    slug = area["slug"]
    short = area["shortName"]
    result = {
        "slug": slug,
        "shortName": short,
        "sourceUrl": None,
        "license": None,
        "wikiTitle": wiki_title_for(area),
        "file": None,
        "webPath": None,
        "status": "missing",
        "note": "",
    }

    candidates: list[tuple[str, str | None]] = []

    override = FILE_OVERRIDES.get(slug)
    if override:
        url, lic = commons_file_url(override)
        if url:
            candidates.append((url, lic))
            result["note"] = f"override:{override}"

    page_url, page_lic, resolved = page_image(result["wikiTitle"])
    if resolved:
        result["wikiTitle"] = resolved
    if page_url:
        # Reject seals/maps/flags from lead images by filename cues.
        low = page_url.lower()
        if not any(bad in low for bad in ("seal", "flag", "locator", "map_", "_map", "coa_", "coat")):
            candidates.append((page_url, page_lic))

    for query in (
        f'{short} Florida downtown',
        f'{short} Florida skyline',
        f'{short} Florida courthouse',
        f'{short} Florida',
    ):
        url, lic = commons_search(query)
        if url:
            candidates.append((url, lic))
            break

    if not candidates:
        # County fallback for tiny cities
        county = area.get("county")
        if county:
            url, lic = commons_search(f"{county} Florida courthouse")
            if url:
                candidates.append((url, lic))
                result["note"] = (result["note"] + "; county-fallback").strip("; ")

    if not candidates:
        return result

    url, lic = candidates[0]
    result["sourceUrl"] = url
    result["license"] = lic or ""
    result["status"] = "resolved"
    return result


def main() -> None:
    areas = json.loads(AREAS_PATH.read_text(encoding="utf-8"))["areas"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict] = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    for i, area in enumerate(areas, 1):
        slug = area["slug"]
        print(f"[{i}/{len(areas)}] {slug} …", flush=True)
        info = resolve_image(area)
        if info["status"] != "resolved" or not info["sourceUrl"]:
            print(f"  MISSING for {slug}")
            manifest[slug] = info
            time.sleep(0.35)
            continue

        ext = Path(urllib.parse.urlparse(info["sourceUrl"]).path).suffix.lower() or ".jpg"
        if ext not in {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}:
            ext = ".jpg"
        raw = OUT_DIR / f"{slug}.src{ext}"
        webp = OUT_DIR / f"{slug}.webp"
        try:
            download(info["sourceUrl"], raw)
            to_webp(raw, webp)
            raw.unlink(missing_ok=True)
            info["file"] = webp.name
            info["webPath"] = f"/assets/images/areas/{webp.name}"
            info["status"] = "ok"
            print(f"  OK <- {info['sourceUrl'][:90]}...")
        except Exception as exc:  # noqa: BLE001
            info["status"] = "error"
            info["note"] = str(exc)
            print(f"  ERROR {exc}")
        manifest[slug] = info
        time.sleep(0.4)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Attach heroImage onto service-areas.json
    payload = json.loads(AREAS_PATH.read_text(encoding="utf-8"))
    for area in payload["areas"]:
        m = manifest.get(area["slug"]) or {}
        if m.get("webPath"):
            area["heroImage"] = m["webPath"]
            area["heroImageCredit"] = {
                "sourceUrl": m.get("sourceUrl"),
                "license": m.get("license"),
                "wikiTitle": m.get("wikiTitle"),
            }
    AREAS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    ok = sum(1 for v in manifest.values() if v.get("status") == "ok")
    print(f"Done: {ok}/{len(areas)} images. Manifest -> {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
