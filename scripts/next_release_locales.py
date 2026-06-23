#!/usr/bin/env python3
"""Locale matrix for the next App Store release package.

The target is 41 public display languages. The concrete locale IDs are 42
because App Store/Xcode may keep Brazilian and European Portuguese separate
while the public product page can display them as one Portuguese language.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReleaseLocale:
    code: str
    display_group: str
    english_name: str
    japanese_name: str
    phase: str
    rtl: bool = False
    complex_text: bool = False


TARGET_LOCALES: tuple[ReleaseLocale, ...] = (
    ReleaseLocale("ar", "ar", "Arabic", "アラビア語", "current", rtl=True, complex_text=True),
    ReleaseLocale("bg", "bg", "Bulgarian", "ブルガリア語", "expansion"),
    ReleaseLocale("bn", "bn", "Bengali", "ベンガル語", "expansion", complex_text=True),
    ReleaseLocale("ca", "ca", "Catalan", "カタロニア語", "quickdrop-parity"),
    ReleaseLocale("cs", "cs", "Czech", "チェコ語", "quickdrop-parity"),
    ReleaseLocale("da", "da", "Danish", "デンマーク語", "quickdrop-parity"),
    ReleaseLocale("de", "de", "German", "ドイツ語", "current"),
    ReleaseLocale("el", "el", "Greek", "ギリシャ語", "quickdrop-parity"),
    ReleaseLocale("en", "en", "English", "英語", "current"),
    ReleaseLocale("es", "es", "Spanish", "スペイン語", "current"),
    ReleaseLocale("et", "et", "Estonian", "エストニア語", "expansion"),
    ReleaseLocale("fi", "fi", "Finnish", "フィンランド語", "quickdrop-parity"),
    ReleaseLocale("fil", "fil", "Filipino", "フィリピン語", "expansion"),
    ReleaseLocale("fr", "fr", "French", "フランス語", "current"),
    ReleaseLocale("he", "he", "Hebrew", "ヘブライ語", "quickdrop-parity", rtl=True, complex_text=True),
    ReleaseLocale("hi", "hi", "Hindi", "ヒンディー語", "quickdrop-parity", complex_text=True),
    ReleaseLocale("hr", "hr", "Croatian", "クロアチア語", "quickdrop-parity"),
    ReleaseLocale("hu", "hu", "Hungarian", "ハンガリー語", "current"),
    ReleaseLocale("id", "id", "Indonesian", "インドネシア語", "quickdrop-parity"),
    ReleaseLocale("it", "it", "Italian", "イタリア語", "current"),
    ReleaseLocale("ja", "ja", "Japanese", "日本語", "current", complex_text=True),
    ReleaseLocale("ko", "ko", "Korean", "韓国語", "current", complex_text=True),
    ReleaseLocale("lt", "lt", "Lithuanian", "リトアニア語", "expansion"),
    ReleaseLocale("lv", "lv", "Latvian", "ラトビア語", "expansion"),
    ReleaseLocale("ms", "ms", "Malay", "マレー語", "quickdrop-parity"),
    ReleaseLocale("nb", "nb", "Norwegian Bokmal", "ノルウェー語（ブークモール）", "quickdrop-parity"),
    ReleaseLocale("nl", "nl", "Dutch", "オランダ語", "current"),
    ReleaseLocale("pl", "pl", "Polish", "ポーランド語", "quickdrop-parity"),
    ReleaseLocale("pt-BR", "pt", "Portuguese (Brazil)", "ポルトガル語（ブラジル）", "current"),
    ReleaseLocale("pt-PT", "pt", "Portuguese (Portugal)", "ポルトガル語（ポルトガル）", "current"),
    ReleaseLocale("ro", "ro", "Romanian", "ルーマニア語", "current"),
    ReleaseLocale("ru", "ru", "Russian", "ロシア語", "current"),
    ReleaseLocale("sk", "sk", "Slovak", "スロバキア語", "expansion"),
    ReleaseLocale("sl", "sl", "Slovenian", "スロベニア語", "expansion"),
    ReleaseLocale("sr", "sr", "Serbian", "セルビア語", "expansion"),
    ReleaseLocale("sv", "sv", "Swedish", "スウェーデン語", "quickdrop-parity"),
    ReleaseLocale("th", "th", "Thai", "タイ語", "current", complex_text=True),
    ReleaseLocale("tr", "tr", "Turkish", "トルコ語", "quickdrop-parity"),
    ReleaseLocale("uk", "uk", "Ukrainian", "ウクライナ語", "current"),
    ReleaseLocale("vi", "vi", "Vietnamese", "ベトナム語", "quickdrop-parity"),
    ReleaseLocale("zh-Hans", "zh-Hans", "Simplified Chinese", "簡体字中国語", "current", complex_text=True),
    ReleaseLocale("zh-Hant", "zh-Hant", "Traditional Chinese", "繁体字中国語", "current", complex_text=True),
)


EXPECTED_SCREENSHOT_FILES = (
    "01-send-to-android.png",
    "02-receive-from-android.png",
    "03-qr-fallback.png",
    "04-pyonta-plus.png",
)


def locale_codes() -> list[str]:
    return [locale.code for locale in TARGET_LOCALES]


def display_language_count() -> int:
    return len({locale.display_group for locale in TARGET_LOCALES})


def phase_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for locale in TARGET_LOCALES:
        counts[locale.phase] = counts.get(locale.phase, 0) + 1
    return counts


def rtl_locale_codes() -> list[str]:
    return [locale.code for locale in TARGET_LOCALES if locale.rtl]


def complex_text_locale_codes() -> list[str]:
    return [locale.code for locale in TARGET_LOCALES if locale.complex_text]
