#!/usr/bin/env python3
"""Compress and convert site images to WebP with responsive variants (ffmpeg)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "assets" / "images"
MANIFEST_PATH = ROOT / "data" / "image-manifest.json"

SOURCE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
SKIP_DIRS = {"icons"}
WIDTHS = (480, 800, 1200, 1600)
HERO_DIR = IMAGES / "hero"
QUALITY = 76
RECOMPRESS_MIN_BYTES = 350_000
MAX_DEFAULT = 1600
MAX_HERO = 1920


def probe_size(path: Path) -> tuple[int, int] | None:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0:s=x",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    line = (proc.stdout or "").strip().splitlines()[0] if proc.stdout else ""
    if "x" not in line:
        return None
    w, h = line.split("x", 1)
    try:
        return int(w), int(h)
    except ValueError:
        return None


def encode_webp(src: Path, dst: Path, max_width: int) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    out = dst
    temp: Path | None = None
    if src.resolve() == dst.resolve():
        temp = dst.with_name(f"{dst.stem}.opt{dst.suffix}")
        out = temp
    vf = f"scale='min({max_width},iw)':-2:flags=lanczos"
    proc = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-vf",
            vf,
            "-c:v",
            "libwebp",
            "-quality",
            str(QUALITY),
            "-compression_level",
            "6",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        if temp and temp.is_file():
            temp.unlink(missing_ok=True)
        print("FAIL", dst.name, (proc.stderr or proc.stdout)[-200:])
        return False
    if not out.is_file() or out.stat().st_size == 0:
        if temp and temp.is_file():
            temp.unlink(missing_ok=True)
        return False
    if temp:
        temp.replace(dst)
    return True


def logical_key(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if not rel.startswith("assets/images/"):
        rel = "assets/images/" + path.relative_to(IMAGES).as_posix()
    return "/" + rel


def variant_path(base_webp: Path, width: int) -> Path:
    return base_webp.with_name(f"{base_webp.stem}-{width}w.webp")


def should_process(path: Path) -> bool:
    if path.suffix.lower() not in SOURCE_EXTS:
        return False
    if any(part in SKIP_DIRS for part in path.parts):
        return False
    if "-social" in path.stem or path.stem.endswith("-640w"):
        return False
    if any(path.stem.endswith(f"-{w}w") for w in WIDTHS):
        return False
    return True


def max_width_for(path: Path) -> int:
    if HERO_DIR in path.parents or path.parent == HERO_DIR:
        return MAX_HERO
    return MAX_DEFAULT


def process_file(path: Path, manifest: dict) -> None:
    if not should_process(path):
        return

    stem = path.stem
    if path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
        base_webp = path.with_suffix(".webp")
        source = path
    else:
        base_webp = path
        source = path

    cap = max_width_for(path)
    size_before = source.stat().st_size
    needs_work = (
        path.suffix.lower() in {".jpg", ".jpeg", ".png"}
        or size_before >= RECOMPRESS_MIN_BYTES
        or (probe_size(source) or (9999, 9999))[0] > cap
    )
    if not needs_work and base_webp.is_file():
        dims = probe_size(base_webp) or (0, 0)
        key = logical_key(base_webp)
        manifest[key] = {
            "src": key,
            "width": dims[0],
            "height": dims[1],
            "variants": {str(w): logical_key(variant_path(base_webp, w)) for w in WIDTHS if variant_path(base_webp, w).is_file()},
        }
        return

    if not encode_webp(source, base_webp, cap):
        return

    dims = probe_size(base_webp) or (0, 0)
    iw = dims[0] or cap
    variants: dict[str, str] = {}
    for w in WIDTHS:
        if iw <= w and w != WIDTHS[-1]:
            continue
        vp = variant_path(base_webp, w)
        if encode_webp(base_webp, vp, w):
            variants[str(w)] = logical_key(vp)

    key = logical_key(base_webp)
    manifest[key] = {
        "src": key,
        "width": dims[0],
        "height": dims[1],
        "variants": variants,
    }
    after = base_webp.stat().st_size
    print(
        f"{'conv' if path.suffix.lower() != '.webp' else 'opt':5} "
        f"{path.relative_to(IMAGES)} -> {base_webp.name} "
        f"{size_before/1024:.0f}KB -> {after/1024:.0f}KB"
    )


def main() -> int:
    manifest: dict = {}
    files = sorted(
        p for p in IMAGES.rglob("*") if p.is_file() and should_process(p)
    )
    print(f"Processing {len(files)} images under {IMAGES}")
    for path in files:
        try:
            process_file(path, manifest)
        except Exception as exc:  # noqa: BLE001
            print("ERROR", path, exc)

    logo_src = IMAGES / "brand" / "Logo-Square-scaled-1024x1024.png"
    logo_dst = IMAGES / "brand" / "logo-96.webp"
    if logo_src.is_file() and encode_webp(logo_src, logo_dst, 96):
        dims = probe_size(logo_dst) or (96, 96)
        manifest["/assets/images/brand/logo-96.webp"] = {
            "src": "/assets/images/brand/logo-96.webp",
            "width": dims[0],
            "height": dims[1],
            "variants": {},
        }
        print(f"logo  {logo_dst.name} ({logo_dst.stat().st_size} bytes)")

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {MANIFEST_PATH} ({len(manifest)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
