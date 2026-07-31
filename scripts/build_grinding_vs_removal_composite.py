#!/usr/bin/env python3
"""Build a grinding-vs-removal comparison composite for the stump portfolio."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "scripts" / "composite-brand.json").read_text(encoding="utf-8"))
OUT = ROOT / "assets" / "images" / "projects" / "stump-removal-portfolio" / "grinding-vs-removal-comparison.webp"
SRC = ROOT / "assets" / "images" / "projects" / "stump-removal-portfolio"


def font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in (
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
        Path(r"C:\Windows\Fonts\segoeuib.ttf"),
    ):
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def hex_color(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def load(path: Path) -> Image.Image:
    with Image.open(path) as source:
        return ImageOps.exif_transpose(source).convert("RGB")


def cover(image: Image.Image, box: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(image, box, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def main() -> int:
    grind = [
        SRC / "stump-grinding-companies-01.webp",
        SRC / "stump-grinding-companies-03.webp",
        SRC / "stump-grinding-after-one-year-01.webp",
    ]
    remove = [
        SRC / "after-01.webp",
        SRC / "after-04.webp",
        SRC / "carrying-a-stump-02.webp",
    ]
    for path in grind + remove:
        if not path.is_file():
            raise SystemExit(f"missing {path}")

    bg = hex_color(CONFIG["background"])
    accent = hex_color(CONFIG["accent"])
    text = hex_color(CONFIG.get("text", "#ffffff"))
    canvas = Image.new("RGB", (1600, 900), bg)
    draw = ImageDraw.Draw(canvas)

    title_font = font(42)
    label_font = font(28)
    small = font(20)
    draw.text((40, 28), "STUMP GRINDING vs STUMP REMOVAL", font=title_font, fill=text)
    draw.text((40, 82), f'{CONFIG["company"]}  •  {CONFIG["phone"]}', font=small, fill=accent)
    draw.rectangle((0, 118, 1600, 122), fill=accent)

    # Two columns
    col_w = 740
    gap = 40
    left_x = 40
    right_x = 40 + col_w + gap
    top = 150
    cell_h = 200
    cell_gap = 16

    draw.rounded_rectangle((left_x - 8, top - 44, left_x + col_w + 8, top - 8), 8, fill=(140, 40, 40))
    draw.text((left_x + 12, top - 40), "GRINDING — roots & chips left behind", font=label_font, fill=text)
    draw.rounded_rectangle((right_x - 8, top - 44, right_x + col_w + 8, top - 8), 8, fill=accent)
    draw.text((right_x + 12, top - 40), "OUR REMOVAL — excavate, haul, restore", font=label_font, fill=bg)

    for i, path in enumerate(grind):
        y = top + i * (cell_h + cell_gap)
        canvas.paste(cover(load(path), (col_w, cell_h)), (left_x, y))
        draw.rectangle((left_x, y, left_x + col_w, y + cell_h), outline=(20, 20, 20), width=3)

    for i, path in enumerate(remove):
        y = top + i * (cell_h + cell_gap)
        canvas.paste(cover(load(path), (col_w, cell_h)), (right_x, y))
        draw.rectangle((right_x, y, right_x + col_w, y + cell_h), outline=(20, 20, 20), width=3)

    draw.rectangle((0, 840, 1600, 900), fill=(20, 20, 20))
    draw.text(
        (40, 858),
        "Grinding is cheaper cosmetics. Excavation clears the mass for fences, pads, and a yard you can actually use.",
        font=small,
        fill=text,
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT, "WEBP", quality=88, method=6)
    social = OUT.with_name(OUT.stem + "-social.jpg")
    canvas.save(social, "JPEG", quality=92, optimize=True)
    print(f"wrote {OUT}")
    print(f"wrote {social}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
