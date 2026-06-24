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

STORE_PACKAGE_DEFAULT = "design/appstore-metadata/next-release/store_package.json"
STORE_IAP_PRODUCT_IDS = {
    "monthly": "com.odiften.pyonta.plus.monthly",
    "yearly": "com.odiften.pyonta.plus.yearly",
    "lifetime": "com.odiften.pyonta.plus.lifetime",
}


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


def audit_store_package(root: Path, expected: set[str], package_path: Path) -> dict[str, Any]:
    path = package_path if package_path.is_absolute() else root / package_path
    if not path.exists():
        return {
            "path": str(path),
            "present": False,
            "ok": False,
            "problems": ["Store package JSON is missing."],
        }

    data = json.loads(path.read_text())
    localizations = data.get("localizations") or {}
    present = set(localizations)
    problems: list[str] = []
    missing = sorted(expected - present)
    extra = sorted(present - expected)
    if missing:
        problems.append("Missing store package locales: " + ", ".join(missing))
    if extra:
        problems.append("Unexpected store package locales: " + ", ".join(extra))

    english = localizations.get("en", {})
    english_version = english.get("versionMetadata", {})
    for locale in sorted(expected & present):
        item = localizations[locale]
        app_info = item.get("appInfo") or {}
        version = item.get("versionMetadata") or {}
        iap = ((item.get("iap") or {}).get("products") or {})
        screenshots = item.get("screenshots") or {}

        required_fields = {
            "appInfo.subtitle": app_info.get("subtitle"),
            "appInfo.privacyPolicyUrl": app_info.get("privacyPolicyUrl"),
            "versionMetadata.description": version.get("description"),
            "versionMetadata.keywords": version.get("keywords"),
            "versionMetadata.promotionalText": version.get("promotionalText"),
            "versionMetadata.supportUrl": version.get("supportUrl"),
            "versionMetadata.marketingUrl": version.get("marketingUrl"),
            "versionMetadata.whatsNew": version.get("whatsNew"),
        }
        empty = [name for name, value in required_fields.items() if not value]
        if empty:
            problems.append(f"{locale}: empty fields: {', '.join(empty)}")

        if len(app_info.get("subtitle", "")) > 30:
            problems.append(f"{locale}: subtitle exceeds 30 characters")
        if len(version.get("keywords", "")) > 100:
            problems.append(f"{locale}: keywords exceed 100 characters")
        if len(version.get("promotionalText", "")) > 170:
            problems.append(f"{locale}: promotionalText exceeds 170 characters")
        if len(version.get("description", "")) > 4000:
            problems.append(f"{locale}: description exceeds 4000 characters")

        if locale != "en":
            for field in ("description", "promotionalText", "whatsNew"):
                if version.get(field) == english_version.get(field):
                    problems.append(f"{locale}: {field} is identical to English fallback")
            if app_info.get("subtitle") == (english.get("appInfo") or {}).get("subtitle"):
                problems.append(f"{locale}: subtitle is identical to English fallback")

        for key, product_id in STORE_IAP_PRODUCT_IDS.items():
            product = iap.get(key)
            if not product:
                problems.append(f"{locale}: missing IAP product {key}")
                continue
            if product.get("productId") != product_id:
                problems.append(f"{locale}: {key} productId mismatch")
            if not product.get("displayName") or not product.get("description"):
                problems.append(f"{locale}: {key} IAP displayName/description missing")

        for file_name in screenshots.get("files") or []:
            screenshot_path = root / screenshots.get("directory", "") / file_name
            if not screenshot_path.exists():
                problems.append(f"{locale}: package screenshot path missing {screenshot_path}")
        review = screenshots.get("reviewScreenshot")
        if review and not (root / review).exists():
            problems.append(f"{locale}: package review screenshot path missing {review}")

    declarations = data.get("accessibilityDeclarations") or {}
    coverage = set(declarations.get("localeCoverage") or [])
    if coverage != expected:
        problems.append("Accessibility declaration localeCoverage does not match target locales")
    if not declarations.get("proposedAfterFinalBinaryAudit"):
        problems.append("Accessibility declaration proposal is empty")

    return {
        "path": str(path),
        "present": True,
        "localizationCount": len(present),
        "missingLocales": missing,
        "extraLocales": extra,
        "accessibilityLocaleCoverageCount": len(coverage),
        "problems": problems,
        "ok": not problems,
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


def build_report(root: Path, screenshot_base: Path, store_package: Path) -> dict[str, Any]:
    expected = set(locale_codes())
    known_regions = parse_known_regions(root / "Pyonta.xcodeproj" / "project.pbxproj")
    screenshot_report = audit_screenshots(root, expected, screenshot_base)
    xcstrings_reports = [audit_xcstrings(root / path, expected) for path in XCSTRINGS_FILES]
    store_package_report = audit_store_package(root, expected, store_package)
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
    if not store_package_report["ok"]:
        warnings.append("Store metadata/IAP/accessibility package audit has problems.")

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
        "storePackage": store_package_report,
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
    store = report["storePackage"]
    print(f"Store package present: {store['present']}")
    if store["present"]:
        print(f"Store package locales: {store['localizationCount']}")
        print(f"Accessibility coverage locales: {store['accessibilityLocaleCoverageCount']}")
    print(f"Store package problems: {len(store['problems'])}")
    for problem in store["problems"][:20]:
        print(f"  - {problem}")
    if len(store["problems"]) > 20:
        print(f"  ... {len(store['problems']) - 20} more")
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
    parser.add_argument(
        "--store-package",
        default=STORE_PACKAGE_DEFAULT,
        help="Local next-release App Store metadata/IAP/accessibility package JSON",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report(Path(args.root).resolve(), Path(args.screenshot_base), Path(args.store_package))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
