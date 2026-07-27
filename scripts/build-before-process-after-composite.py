#!/usr/bin/env python3
"""Build a branded 1600x900 before/process/after proof composite."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "scripts" / "composite-brand.json").read_text(encoding="utf-8"))
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff", ".bmp"}


def font(size: int, *, serif: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        [Path(r"C:\Windows\Fonts\georgiab.ttf"), Path(r"C:\Windows\Fonts\timesbd.ttf")]
        if serif
        else [Path(r"C:\Windows\Fonts\arialbd.ttf"), Path(r"C:\Windows\Fonts\segoeuib.ttf")]
    )
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def hex_color(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def load_image(path: Path) -> Image.Image:
    with Image.open(path) as source:
        return ImageOps.exif_transpose(source).convert("RGB")


def collect(folder: Path) -> dict[str, list[Path]]:
    result = {"before": [], "process": [], "after": []}
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
            continue
        lower = path.stem.lower()
        for kind in result:
            if lower.startswith(kind):
                result[kind].append(path)
                break
    if not result["before"] or not result["after"]:
        raise SystemExit("At least one before and one after image are required")
    # Balanced cap: preserve each phase, then fill remaining cells.
    selected = {kind: paths[:1] for kind, paths in result.items() if paths}
    remaining = 8 - sum(len(v) for v in selected.values())
    while remaining:
        added = False
        for kind in ("before", "process", "after"):
            current = selected.setdefault(kind, [])
            source = result[kind]
            if len(current) < len(source):
                current.append(source[len(current)])
                remaining -= 1
                added = True
                if not remaining:
                    break
        if not added:
            break
    return {kind: paths for kind, paths in selected.items() if paths}


def fit_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, start: int, *, serif: bool = False):
    size = start
    while size > 24:
        chosen = font(size, serif=serif)
        if draw.textbbox((0, 0), text, font=chosen)[2] <= max_width:
            return chosen
        size -= 2
    return font(24, serif=serif)


def cover(image: Image.Image, box: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(image, box, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def paste_logo(canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
    path = ROOT / CONFIG["logo"]
    if not path.is_file():
        return
    with Image.open(path) as source:
        logo = ImageOps.exif_transpose(source).convert("RGBA")
    logo.thumbnail((165, 165), Image.Resampling.LANCZOS)
    x, y = 26, 18 + (160 - logo.height) // 2
    if CONFIG.get("logo_panel"):
        draw.rounded_rectangle((20, 22, 194, 176), 16, fill=hex_color(CONFIG.get("logo_panel_color", "#f2f8fc")))
    canvas.paste(logo, (x, y), logo)


def build(folder: Path, title: str, out_dir: Path, basename: str) -> dict[str, Path]:
    phases = collect(folder)
    bg = hex_color(CONFIG["background"])
    accent = hex_color(CONFIG["accent"])
    surface = hex_color(CONFIG["surface"])
    text = hex_color(CONFIG.get("text", "#ffffff"))
    muted = hex_color(CONFIG.get("muted", "#c9c9c9"))
    canvas = Image.new("RGB", (1600, 900), bg)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 195, 1600, 200), fill=accent)
    draw.rectangle((0, 784, 1600, 789), fill=accent)
    paste_logo(canvas, draw)

    title_font = fit_text(draw, title.upper(), 950, 58, serif=CONFIG.get("serif_title", False))
    title_box = draw.textbbox((0, 0), title.upper(), font=title_font)
    draw.text((210, 82 - (title_box[3] - title_box[1]) / 2), title.upper(), font=title_font, fill=text)
    info_font = font(25, serif=CONFIG.get("serif_title", False))
    small_font = font(19)
    right = 1565
    company = CONFIG["company"]
    width = draw.textbbox((0, 0), company, font=info_font)[2]
    draw.text((right - width, 45), company, font=info_font, fill=accent)
    contact = f'{CONFIG["phone"]}  •  {CONFIG["email"]}'
    width = draw.textbbox((0, 0), contact, font=small_font)[2]
    draw.text((right - width, 90), contact, font=small_font, fill=text)
    area = CONFIG["area"]
    width = draw.textbbox((0, 0), area, font=small_font)[2]
    draw.text((right - width, 126), area, font=small_font, fill=muted)

    phase_names = list(phases)
    gap, side = 18, 34
    column_width = (1600 - side * 2 - gap * (len(phase_names) - 1)) // len(phase_names)
    top, bottom = 245, 760
    label_font = font(28, serif=CONFIG.get("serif_title", False))
    for column, kind in enumerate(phase_names):
        left = side + column * (column_width + gap)
        right_x = left + column_width
        label = kind.upper()
        label_width = draw.textbbox((0, 0), label, font=label_font)[2]
        tab_left = left + (column_width - max(190, label_width + 50)) // 2
        draw.rounded_rectangle((tab_left, 207, tab_left + max(190, label_width + 50), 247), 8, fill=accent)
        draw.text((left + (column_width - label_width) / 2, 211), label, font=label_font, fill=bg)
        draw.rounded_rectangle((left, top, right_x, bottom), 12, fill=surface, outline=accent, width=2)
        paths = phases[kind]
        count = len(paths)
        rows = math.ceil(count / 2) if count > 1 else 1
        cols = 2 if count > 1 else 1
        inner_gap = 8
        cell_w = (column_width - 16 - inner_gap * (cols - 1)) // cols
        cell_h = (bottom - top - 16 - inner_gap * (rows - 1)) // rows
        for idx, path in enumerate(paths):
            row, col = divmod(idx, cols)
            x = left + 8 + col * (cell_w + inner_gap)
            y = top + 8 + row * (cell_h + inner_gap)
            image = cover(load_image(path), (cell_w, cell_h))
            canvas.paste(image, (x, y))
            draw.rectangle((x, y, x + cell_w, y + cell_h), outline=(15, 15, 15), width=3)
            # Number badge (01, 02…) matching process/angle captions on project pages
            badge = f"{idx + 1:02d}"
            badge_font = font(max(18, min(28, cell_h // 8)))
            bw = draw.textbbox((0, 0), badge, font=badge_font)[2]
            bh = draw.textbbox((0, 0), badge, font=badge_font)[3]
            pad = 6
            bx1, by1 = x + 8, y + 8
            bx2, by2 = bx1 + bw + pad * 2, by1 + bh + pad
            draw.rounded_rectangle((bx1, by1, bx2, by2), 6, fill=accent)
            draw.text((bx1 + pad, by1 + 2), badge, font=badge_font, fill=bg)

    footer_title = font(28, serif=CONFIG.get("serif_title", False))
    footer_small = font(20)
    draw.text((44, 813), CONFIG["services"], font=footer_title, fill=text)
    draw.text((44, 855), f'{CONFIG["website"]}  •  {CONFIG["email"]}', font=footer_small, fill=accent)
    area_width = draw.textbbox((0, 0), CONFIG["footer_area"], font=footer_small)[2]
    draw.text((1556 - area_width, 838), CONFIG["footer_area"], font=footer_small, fill=muted)

    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "webp": out_dir / f"{basename}.webp",
        "webp_640": out_dir / f"{basename}-640w.webp",
        "social_jpg": out_dir / f"{basename}-social.jpg",
    }
    canvas.save(paths["webp"], "WEBP", quality=88, method=6)
    canvas.resize((640, 360), Image.Resampling.LANCZOS).save(paths["webp_640"], "WEBP", quality=86, method=6)
    canvas.save(paths["social_jpg"], "JPEG", quality=92, optimize=True, progressive=True)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--basename", required=True)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--also-jpeg", action="store_true", help="Accepted for Dispatch compatibility")
    args = parser.parse_args()
    outputs = build(args.folder, args.title, args.out or ROOT / CONFIG["gallery_dir"], args.basename)
    print(json.dumps({key: str(value) for key, value in outputs.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
