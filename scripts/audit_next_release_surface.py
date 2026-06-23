#!/usr/bin/env python3
"""Audit the next Pyonta App Store release surface locally.

This is intentionally read-only. It checks local repo artifacts against the
next release target: app binary localizations, screenshot files, and Xcode's
known region list. App Store Connect mutations remain a manual stop point.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from next_release_locales import (
    EXPECTED_SCREENSHOT_FILES,
    TARGET_LOCALES,
    complex_text_locale_codes,
    display_language_count,
    locale_codes,
    phase_counts,
    rtl_locale_codes,
)


XCSTRINGS_FILES = (
    "Pyonta/Localizable.xcstrings",
    "ShareExtension/Localizable.xcstrings",
    "Pyonta/Pyonta-InfoPlist.xcstrings",
    "Pyonta/mul.lproj/SendViewController.xcstrings",
    "ShareExtension/mul.lproj/ShareViewController.xcstrings",
)


def parse_known_regions(project_file: Path) -> set[str]:
    text = project_file.read_text()
    match = re.search(r"knownRegions = \(\n(?P<body>.*?)\n\s*\);", text, re.S)
    if not match:
        return set()
    regions: set[str] = set()
    for raw in match.group("body").splitlines():
        value = raw.strip().rstrip(",").strip('"')
        if value:
            regions.add(value)
    return regions


def audit_xcstrings(path: Path, expected: set[str]) -> dict[str, Any]:
    data = json.loads(path.read_text())
    source_language = data.get("sourceLanguage")
    missing_by_key: dict[str, list[str]] = {}
    for key, value in data.get("strings", {}).items():
        localizations = set((value.get("localizations") or {}).keys())
        effective = set(localizations)
        if source_language:
            effective.add(source_language)
        missing = sorted(expected - effective)
        if missing:
            missing_by_key[key] = missing
    missing_locales = sorted({loc for missing in missing_by_key.values() for loc in missing})
    return {
        "path": str(path),
        "sourceLanguage": source_language,
        "stringCount": len(data.get("strings", {})),
        "keysWithMissingLocales": len(missing_by_key),
        "missingLocales": missing_locales,
        "sampleMissing": dict(list(missing_by_key.items())[:5]),
    }


def audit_screenshots(root: Path, expected: set[str], screenshot_base: Path) -> dict[str, Any]:
    base = screenshot_base if screenshot_base.is_absolute() else root / screenshot_base
    locales: dict[str, Any] = {}
    for locale in sorted(expected):
        directory = base / locale
        missing_files = [name for name in EXPECTED_SCREENSHOT_FILES if not (directory / name).exists()]
        locales[locale] = {
            "directory": str(directory),
            "present": directory.exists(),
            "missingFiles": missing_files,
            "complete": directory.exists() and not missing_files,
        }
    review_dir = base / "review"
    review_missing = [
        locale
        for locale in sorted(expected)
        if not (review_dir / f"pyonta-plus-required-{locale}-2880x1800.png").exists()
    ]
    incomplete = [locale for locale, value in locales.items() if not value["complete"]]
    return {
        "base": str(base),
        "completeLocales": sorted(set(locales) - set(incomplete)),
        "incompleteLocales": incomplete,
        "reviewScreenshotMissingLocales": review_missing,
        "locales": locales,
    }


def pillow_text_shaping_state() -> dict[str, Any]:
    try:
        from PIL import features
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"available": False, "error": str(exc)}
    return {
        "available": True,
        "raqm": bool(features.check("raqm")),
        "fribidi": bool(features.check("fribidi")),
        "harfbuzz": bool(features.check("harfbuzz")),
    }


def core_text_renderer_state(root: Path) -> dict[str, Any]:
    script = root / "scripts" / "render_text_coretext.swift"
    return {
        "available": script.exists(),
        "script": str(script),
    }


def build_report(root: Path, screenshot_base: Path) -> dict[str, Any]:
    expected = set(locale_codes())
    known_regions = parse_known_regions(root / "Pyonta.xcodeproj" / "project.pbxproj")
    screenshot_report = audit_screenshots(root, expected, screenshot_base)
    xcstrings_reports = [audit_xcstrings(root / path, expected) for path in XCSTRINGS_FILES]
    text_shaping = pillow_text_shaping_state()
    core_text = core_text_renderer_state(root)
    warnings: list[str] = []
    if not text_shaping.get("raqm") and not core_text["available"]:
        warnings.append(
            "No complex-script text renderer is available; RTL and complex-script screenshots need visual review."
        )
    if screenshot_report["incompleteLocales"]:
        warnings.append("Some target locales do not have a complete 4-image App Store screenshot set.")
    if any(report["keysWithMissingLocales"] for report in xcstrings_reports):
        warnings.append("Some .xcstrings catalogs are missing target binary UI locales.")
    missing_known_regions = sorted(expected - known_regions)
    if missing_known_regions:
        warnings.append("Xcode knownRegions is missing target locales.")

    return {
        "target": {
            "localeIdCount": len(TARGET_LOCALES),
            "displayLanguageCount": display_language_count(),
            "phaseCounts": phase_counts(),
            "localeCodes": locale_codes(),
            "rtlLocales": rtl_locale_codes(),
            "complexTextLocales": complex_text_locale_codes(),
        },
        "xcode": {
            "knownRegionsCount": len(known_regions),
            "missingKnownRegions": missing_known_regions,
            "extraKnownRegions": sorted(known_regions - expected - {"Base"}),
        },
        "xcstrings": xcstrings_reports,
        "screenshots": screenshot_report,
        "textShaping": text_shaping,
        "coreTextRenderer": core_text,
        "warnings": warnings,
        "ok": not warnings,
    }


def print_human(report: dict[str, Any]) -> None:
    target = report["target"]
    print(
        f"Target: {target['localeIdCount']} locale IDs, "
        f"{target['displayLanguageCount']} public display languages"
    )
    print(f"Phase counts: {target['phaseCounts']}")
    print()
    print(f"Xcode knownRegions missing: {len(report['xcode']['missingKnownRegions'])}")
    if report["xcode"]["missingKnownRegions"]:
        print("  " + ", ".join(report["xcode"]["missingKnownRegions"]))
    print()
    for item in report["xcstrings"]:
        print(Path(item["path"]).name)
        print(
            f"  strings={item['stringCount']} "
            f"keysWithMissingLocales={item['keysWithMissingLocales']}"
        )
        if item["missingLocales"]:
            print("  missingLocales=" + ", ".join(item["missingLocales"]))
    print()
    screenshots = report["screenshots"]
    print(f"Screenshot complete locales: {len(screenshots['completeLocales'])}")
    print(f"Screenshot incomplete locales: {len(screenshots['incompleteLocales'])}")
    if screenshots["incompleteLocales"]:
        print("  " + ", ".join(screenshots["incompleteLocales"]))
    print(f"Review screenshot missing locales: {len(screenshots['reviewScreenshotMissingLocales'])}")
    if screenshots["reviewScreenshotMissingLocales"]:
        print("  " + ", ".join(screenshots["reviewScreenshotMissingLocales"]))
    print()
    print(f"Pillow text shaping: {report['textShaping']}")
    print(f"CoreText renderer: {report['coreTextRenderer']}")
    if report["warnings"]:
        print()
        print("Warnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument(
        "--screenshot-base",
        default="design/appstore-screenshots",
        help="Directory containing per-locale screenshot folders",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report(Path(args.root).resolve(), Path(args.screenshot_base))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
