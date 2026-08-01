#!/usr/bin/env python3
"""Submit breakinggroundlsad.com sitemap URLs to IndexNow (Bing/Yandex)."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY = "0e914d9815b99d4daab617a77b50ccac"
HOST = "breakinggroundlsad.com"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/IndexNow"


def load_urls() -> list[str]:
    tree = ET.parse(ROOT / "sitemap.xml")
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [
        loc.text.strip()
        for loc in tree.findall(".//sm:loc", ns)
        if loc.text and loc.text.strip()
    ]
    if not urls:
        raise SystemExit("No URLs found in sitemap.xml")
    return urls


def main() -> None:
    urls = load_urls()
    payload = json.dumps(
        {
            "host": HOST,
            "key": KEY,
            "keyLocation": KEY_LOCATION,
            "urlList": urls,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(f"IndexNow status: {response.status}")
            print(f"Submitted {len(urls)} URLs for {HOST}")
            if body:
                print(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"IndexNow HTTP error: {exc.code}", file=sys.stderr)
        print(body, file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
