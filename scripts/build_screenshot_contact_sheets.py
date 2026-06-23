#!/usr/bin/env python3
"""Build App Store thumbnail-scale contact sheets for visual review."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from next_release_locales import EXPECTED_SCREENSHOT_FILES, TARGET_LOCALES


JA_ONLY_FILES = (
    ("01 MacからAndroid", "ja/01-send-to-android.png"),
    ("02 AndroidからMac", "ja/02-receive-from-android.png"),
    ("03 QRでも送信", "ja/03-qr-fallback.png"),
    ("04 Pyonta+", "ja/04-pyonta-plus.png"),
    ("審査用", "review/pyonta-plus-required-ja-2880x1800.png"),
)


def font(size: int) -> ImageFont.FreeTypeFont:
    for path in (
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def build_sheet(
    base: Path,
    output: Path,
    screenshot_name: str | None,
    thumb: tuple[int, int],
    columns: int,
    *,
    review: bool = False,
) -> None:
    rows = (len(TARGET_LOCALES) + columns - 1) // columns
    label_h = 34
    gap = 18
    margin = 24
    width = margin * 2 + columns * thumb[0] + (columns - 1) * gap
    height = margin * 2 + rows * (thumb[1] + label_h) + (rows - 1) * gap
    sheet = Image.new("RGB", (width, height), "#F4F6F3")
    draw = ImageDraw.Draw(sheet)
    fnt = font(18)

    for index, locale in enumerate(TARGET_LOCALES):
        row = index // columns
        col = index % columns
        x = margin + col * (thumb[0] + gap)
        y = margin + row * (thumb[1] + label_h + gap)
        if review:
            path = base / "review" / f"pyonta-plus-required-{locale.code}-2880x1800.png"
        else:
            assert screenshot_name is not None
            path = base / locale.code / screenshot_name
        if path.exists():
            image = Image.open(path).convert("RGB").resize(thumb, Image.Resampling.LANCZOS)
            sheet.paste(image, (x, y + label_h))
        else:
            draw.rectangle((x, y + label_h, x + thumb[0], y + label_h + thumb[1]), fill="#FFFFFF", outline="#D7DEE5")
            draw.text((x + 12, y + label_h + 12), "missing", font=fnt, fill="#A33")
        draw.text((x, y), locale.code, font=fnt, fill="#18202A")

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, optimize=True)


def build_ja_only_sheet(base: Path, output: Path, thumb: tuple[int, int]) -> None:
    columns = 2
    rows = (len(JA_ONLY_FILES) + columns - 1) // columns
    label_h = 42
    gap = 26
    margin = 32
    width = margin * 2 + columns * thumb[0] + (columns - 1) * gap
    height = margin * 2 + rows * (thumb[1] + label_h) + (rows - 1) * gap
    sheet = Image.new("RGB", (width, height), "#F4F6F3")
    draw = ImageDraw.Draw(sheet)
    fnt = font(22)

    for index, (label, relative_path) in enumerate(JA_ONLY_FILES):
        row = index // columns
        col = index % columns
        x = margin + col * (thumb[0] + gap)
        y = margin + row * (thumb[1] + label_h + gap)
        path = base / relative_path
        draw.text((x, y), label, font=fnt, fill="#18202A")
        if path.exists():
            image = Image.open(path).convert("RGB").resize(thumb, Image.Resampling.LANCZOS)
            sheet.paste(image, (x, y + label_h))
        else:
            draw.rectangle((x, y + label_h, x + thumb[0], y + label_h + thumb[1]), fill="#FFFFFF", outline="#D7DEE5")
            draw.text((x + 12, y + label_h + 12), "missing", font=fnt, fill="#A33")

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--screenshot-base", default="design/appstore-screenshots/next-release")
    parser.add_argument("--output-dir", default="design/appstore-screenshots/next-release-contact-sheets")
    parser.add_argument("--thumb-width", type=int, default=360)
    parser.add_argument("--columns", type=int, default=6)
    args = parser.parse_args()

    base = Path(args.screenshot_base)
    if not base.exists():
        raise SystemExit(f"Screenshot base not found: {base}")
    thumb = (args.thumb_width, round(args.thumb_width * 1800 / 2880))
    output_dir = Path(args.output_dir)
    for screenshot_name in EXPECTED_SCREENSHOT_FILES:
        output = output_dir / screenshot_name.replace(".png", "-contact.png")
        build_sheet(base, output, screenshot_name, thumb, args.columns)
        print(output)
    output = output_dir / "review-pyonta-plus-required-contact.png"
    build_sheet(base, output, None, thumb, args.columns, review=True)
    print(output)
    output = output_dir / "ja-only-appstore-images.png"
    build_ja_only_sheet(base, output, (args.thumb_width * 2, round(args.thumb_width * 2 * 1800 / 2880)))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
