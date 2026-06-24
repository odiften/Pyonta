#!/usr/bin/env python3
"""Build local App Store copy drafts for the next Pyonta release.

This script does not call App Store Connect. It creates a local package that
can be audited before any live metadata, IAP, screenshot, or accessibility
changes are made.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from next_release_locales import (
    EXPECTED_SCREENSHOT_FILES,
    TARGET_LOCALES,
    display_language_count,
    locale_codes,
)


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_SCRIPT = ROOT / "design" / "appstore-screenshots" / "generate_next_release_screenshots.py"
LOCALIZABLE = ROOT / "Pyonta" / "Localizable.xcstrings"
DEFAULT_OUTPUT = ROOT / "design" / "appstore-metadata" / "next-release" / "store_package.json"

PRIVACY_URL = "https://odiften.com/pyonta/privacy"
TERMS_URL = "https://www.apple.com/legal/internet-services/itunes/dev/stdeula/"
MARKETING_URL = "https://odiften.com"
SUPPORT_URL = PRIVACY_URL

ASC_LOCALE_CANDIDATES = {
    "ar": "ar-SA",
    "de": "de-DE",
    "en": "en-US",
    "es": "es-ES",
    "fr": "fr-FR",
    "nb": "no",
    "nl": "nl-NL",
}

ASC_METADATA_UNSUPPORTED_LOCALES = {
    "bg",
    "bn",
    "et",
    "fil",
    "lt",
    "lv",
    "sl",
    "sr",
}

SUBTITLE_OVERRIDES = {
    "bg": "Android файлове за Mac",
    "ca": "Fitxers Android a Mac",
    "es": "Archivos Android a Mac",
    "pt-BR": "Arquivos Android no Mac",
    "pt-PT": "Ficheiros Android no Mac",
}

IAP_SHORT_DESCRIPTIONS = {
    "ar": "استقبال Android على Mac مع Pyonta+",
    "bg": "Получавайте от Android на Mac с Pyonta+",
    "bn": "Pyonta+ দিয়ে Android থেকে Mac-এ নিন",
    "ca": "Rep d'Android al Mac amb Pyonta+",
    "cs": "Příjem z Androidu na Mac s Pyonta+",
    "da": "Modtag fra Android på Mac med Pyonta+",
    "de": "Android-Empfang auf dem Mac mit Pyonta+",
    "el": "Λήψη από Android σε Mac με Pyonta+",
    "en": "Receive Android files on Mac with Pyonta+.",
    "es": "Recibe de Android en Mac con Pyonta+",
    "et": "Võta Androidist Maci vastu Pyonta+ abil",
    "fi": "Vastaanota Androidista Maciin Pyonta+:lla",
    "fil": "Tumanggap mula Android sa Mac gamit Pyonta+",
    "fr": "Recevez Android sur Mac avec Pyonta+",
    "he": "קבלה מ-Android ל-Mac עם Pyonta+",
    "hi": "Pyonta+ से Android फ़ाइलें Mac पर पाएं",
    "hr": "Primajte s Androida na Mac uz Pyonta+",
    "hu": "Fogadás Androidról Macre Pyonta+-szal",
    "id": "Terima dari Android ke Mac dengan Pyonta+",
    "it": "Ricevi da Android su Mac con Pyonta+",
    "ja": "AndroidからMacへ受信するPyonta+",
    "ko": "Pyonta+로 Android에서 Mac으로 받기",
    "lt": "Gaukite iš Android į Mac su Pyonta+",
    "lv": "Saņemiet no Android uz Mac ar Pyonta+",
    "ms": "Terima Android ke Mac dengan Pyonta+",
    "nb": "Motta fra Android på Mac med Pyonta+",
    "nl": "Ontvang van Android op Mac met Pyonta+",
    "pl": "Odbieraj z Androida na Macu z Pyonta+",
    "pt-BR": "Receba do Android no Mac com Pyonta+",
    "pt-PT": "Receba do Android no Mac com Pyonta+",
    "ro": "Primește din Android pe Mac cu Pyonta+",
    "ru": "Прием с Android на Mac через Pyonta+",
    "sk": "Príjem z Androidu na Mac s Pyonta+",
    "sl": "Prejem z Androida na Mac s Pyonta+",
    "sr": "Примајте са Android-а на Mac уз Pyonta+",
    "sv": "Ta emot från Android på Mac med Pyonta+",
    "th": "รับจาก Android บน Mac ด้วย Pyonta+",
    "tr": "Android'den Mac'e Pyonta+ ile alın",
    "uk": "Отримуйте з Android на Mac з Pyonta+",
    "vi": "Nhận từ Android sang Mac bằng Pyonta+",
    "zh-Hans": "用 Pyonta+ 在 Mac 接收 Android 文件",
    "zh-Hant": "用 Pyonta+ 在 Mac 接收 Android 檔案",
}

TERMS = {
    "ar": {
        "monthly": "شهري",
        "yearly": "سنوي",
        "lifetime": "مدى الحياة",
        "whatsNew": "يضيف 41 لغة عرض عبر التطبيق وصفحة المتجر واللقطات ونص Pyonta+ ومعلومات إمكانية الوصول.",
        "nonAffiliation": "Pyonta مستقل وليس تابعا لـ Google أو Apple.",
    },
    "bg": {
        "monthly": "Месечен",
        "yearly": "Годишен",
        "lifetime": "Доживотен",
        "whatsNew": "Добавя 41 езика за показване в приложението, Store страницата, снимките, текста на Pyonta+ и информацията за достъпност.",
        "nonAffiliation": "Pyonta е независим и не е свързан с Google или Apple.",
    },
    "bn": {
        "monthly": "মাসিক",
        "yearly": "বার্ষিক",
        "lifetime": "আজীবন",
        "whatsNew": "অ্যাপ, Store পৃষ্ঠা, স্ক্রিনশট, Pyonta+ লেখা ও অ্যাক্সেসিবিলিটি তথ্যে ৪১টি প্রদর্শন ভাষা যোগ করা হয়েছে।",
        "nonAffiliation": "Pyonta স্বাধীন এবং Google বা Apple-এর সঙ্গে সংশ্লিষ্ট নয়।",
    },
    "ca": {
        "monthly": "Mensual",
        "yearly": "Anual",
        "lifetime": "De per vida",
        "whatsNew": "Afegeix 41 idiomes de visualització a l'app, la pàgina de la Store, les captures, el text de Pyonta+ i la informació d'accessibilitat.",
        "nonAffiliation": "Pyonta és independent i no està afiliat a Google ni a Apple.",
    },
    "cs": {
        "monthly": "Měsíční",
        "yearly": "Roční",
        "lifetime": "Doživotní",
        "whatsNew": "Přidává 41 jazyků zobrazení pro aplikaci, stránku Store, snímky, text Pyonta+ a informace o přístupnosti.",
        "nonAffiliation": "Pyonta je nezávislá aplikace a není spojena se společnostmi Google ani Apple.",
    },
    "da": {
        "monthly": "Månedlig",
        "yearly": "Årlig",
        "lifetime": "Livstid",
        "whatsNew": "Tilføjer 41 visningssprog på tværs af appen, Store-siden, skærmbilleder, Pyonta+-tekst og tilgængelighedsoplysninger.",
        "nonAffiliation": "Pyonta er uafhængig og ikke tilknyttet Google eller Apple.",
    },
    "de": {
        "monthly": "Monatlich",
        "yearly": "Jährlich",
        "lifetime": "Lebenslang",
        "whatsNew": "Ergänzt 41 Anzeigesprachen für App, Store-Seite, Screenshots, Pyonta+-Text und Bedienungshilfen.",
        "nonAffiliation": "Pyonta ist unabhängig und nicht mit Google oder Apple verbunden.",
    },
    "el": {
        "monthly": "Μηνιαίο",
        "yearly": "Ετήσιο",
        "lifetime": "Εφ' όρου ζωής",
        "whatsNew": "Προσθέτει 41 γλώσσες εμφάνισης στην εφαρμογή, τη σελίδα Store, τα στιγμιότυπα, το κείμενο Pyonta+ και τις πληροφορίες προσβασιμότητας.",
        "nonAffiliation": "Το Pyonta είναι ανεξάρτητο και δεν συνδέεται με την Google ή την Apple.",
    },
    "en": {
        "monthly": "Monthly",
        "yearly": "Yearly",
        "lifetime": "Lifetime",
        "whatsNew": "Adds 41 display languages across the app, Store page, screenshots, Pyonta+ text, and accessibility information.",
        "nonAffiliation": "Pyonta is independent and is not affiliated with Google or Apple.",
    },
    "es": {
        "monthly": "Mensual",
        "yearly": "Anual",
        "lifetime": "De por vida",
        "whatsNew": "Añade 41 idiomas de visualización en la app, la página de Store, las capturas, el texto de Pyonta+ y la información de accesibilidad.",
        "nonAffiliation": "Pyonta es independiente y no está afiliada a Google ni a Apple.",
    },
    "et": {
        "monthly": "Kuu",
        "yearly": "Aasta",
        "lifetime": "Eluaegne",
        "whatsNew": "Lisab 41 kuvamiskeelt rakendusse, Store'i lehele, kuvatõmmistele, Pyonta+ tekstile ja ligipääsetavuse teabele.",
        "nonAffiliation": "Pyonta on sõltumatu ega ole seotud Google'i ega Apple'iga.",
    },
    "fi": {
        "monthly": "Kuukausi",
        "yearly": "Vuosi",
        "lifetime": "Elinikäinen",
        "whatsNew": "Lisää 41 näyttökieltä appiin, Store-sivulle, kuvakaappauksiin, Pyonta+-tekstiin ja saavutettavuustietoihin.",
        "nonAffiliation": "Pyonta on itsenäinen eikä ole Googlen tai Applen kumppani.",
    },
    "fil": {
        "monthly": "Buwanang",
        "yearly": "Taunan",
        "lifetime": "Panghabambuhay",
        "whatsNew": "Nagdaragdag ng 41 display language sa app, Store page, screenshots, Pyonta+ text, at accessibility information.",
        "nonAffiliation": "Independent ang Pyonta at hindi ito kaakibat ng Google o Apple.",
    },
    "fr": {
        "monthly": "Mensuel",
        "yearly": "Annuel",
        "lifetime": "À vie",
        "whatsNew": "Ajoute 41 langues d'affichage dans l'app, la page Store, les captures, le texte Pyonta+ et les informations d'accessibilité.",
        "nonAffiliation": "Pyonta est indépendant et n'est pas affilié à Google ni à Apple.",
    },
    "he": {
        "monthly": "חודשי",
        "yearly": "שנתי",
        "lifetime": "לכל החיים",
        "whatsNew": "מוסיף 41 שפות תצוגה באפליקציה, בעמוד ה-Store, בצילומי המסך, בטקסט Pyonta+ ובמידע הנגישות.",
        "nonAffiliation": "Pyonta עצמאי ואינו קשור ל-Google או ל-Apple.",
    },
    "hi": {
        "monthly": "मासिक",
        "yearly": "वार्षिक",
        "lifetime": "लाइफटाइम",
        "whatsNew": "ऐप, Store पेज, स्क्रीनशॉट, Pyonta+ टेक्स्ट और एक्सेसिबिलिटी जानकारी में 41 डिस्प्ले भाषाएं जोड़ी गईं।",
        "nonAffiliation": "Pyonta स्वतंत्र है और Google या Apple से संबद्ध नहीं है।",
    },
    "hr": {
        "monthly": "Mjesečno",
        "yearly": "Godišnje",
        "lifetime": "Doživotno",
        "whatsNew": "Dodaje 41 jezika prikaza u aplikaciji, Store stranici, snimkama zaslona, Pyonta+ tekstu i informacijama o pristupačnosti.",
        "nonAffiliation": "Pyonta je neovisan i nije povezan s Googleom ili Appleom.",
    },
    "hu": {
        "monthly": "Havi",
        "yearly": "Éves",
        "lifetime": "Élettartam",
        "whatsNew": "41 megjelenítési nyelvet ad az apphoz, a Store-oldalhoz, a képernyőképekhez, a Pyonta+-szöveghez és az akadálymentességi információkhoz.",
        "nonAffiliation": "A Pyonta független, és nem áll kapcsolatban a Google-lel vagy az Apple-lel.",
    },
    "id": {
        "monthly": "Bulanan",
        "yearly": "Tahunan",
        "lifetime": "Seumur hidup",
        "whatsNew": "Menambahkan 41 bahasa tampilan di app, halaman Store, screenshot, teks Pyonta+, dan informasi aksesibilitas.",
        "nonAffiliation": "Pyonta bersifat independen dan tidak berafiliasi dengan Google atau Apple.",
    },
    "it": {
        "monthly": "Mensile",
        "yearly": "Annuale",
        "lifetime": "A vita",
        "whatsNew": "Aggiunge 41 lingue di visualizzazione nell'app, nella pagina Store, negli screenshot, nei testi Pyonta+ e nelle informazioni di accessibilità.",
        "nonAffiliation": "Pyonta è indipendente e non è affiliata a Google o Apple.",
    },
    "ja": {
        "monthly": "月額",
        "yearly": "年額",
        "lifetime": "買い切り",
        "whatsNew": "アプリ、Storeページ、スクリーンショット、Pyonta+文言、アクセシビリティ情報の41表示言語対応を追加しました。",
        "nonAffiliation": "Pyontaは独立したアプリであり、GoogleまたはAppleと提携していません。",
    },
    "ko": {
        "monthly": "월간",
        "yearly": "연간",
        "lifetime": "평생",
        "whatsNew": "앱, Store 페이지, 스크린샷, Pyonta+ 문구, 접근성 정보에 41개 표시 언어를 추가했습니다.",
        "nonAffiliation": "Pyonta는 독립 앱이며 Google 또는 Apple과 제휴하지 않았습니다.",
    },
    "lt": {
        "monthly": "Mėnesinis",
        "yearly": "Metinis",
        "lifetime": "Visam laikui",
        "whatsNew": "Prideda 41 rodymo kalbą programoje, Store puslapyje, ekrano kopijose, Pyonta+ tekste ir prieinamumo informacijoje.",
        "nonAffiliation": "Pyonta yra nepriklausoma ir nėra susijusi su Google ar Apple.",
    },
    "lv": {
        "monthly": "Mēneša",
        "yearly": "Gada",
        "lifetime": "Mūža",
        "whatsNew": "Pievieno 41 attēlojuma valodu lietotnē, Store lapā, ekrānuzņēmumos, Pyonta+ tekstā un piekļūstamības informācijā.",
        "nonAffiliation": "Pyonta ir neatkarīga un nav saistīta ar Google vai Apple.",
    },
    "ms": {
        "monthly": "Bulanan",
        "yearly": "Tahunan",
        "lifetime": "Seumur hidup",
        "whatsNew": "Menambah 41 bahasa paparan pada app, halaman Store, tangkapan skrin, teks Pyonta+ dan maklumat kebolehcapaian.",
        "nonAffiliation": "Pyonta adalah bebas dan tidak bergabung dengan Google atau Apple.",
    },
    "nb": {
        "monthly": "Månedlig",
        "yearly": "Årlig",
        "lifetime": "Livstid",
        "whatsNew": "Legger til 41 visningsspråk i appen, Store-siden, skjermbilder, Pyonta+-tekst og tilgjengelighetsinformasjon.",
        "nonAffiliation": "Pyonta er uavhengig og ikke tilknyttet Google eller Apple.",
    },
    "nl": {
        "monthly": "Maandelijks",
        "yearly": "Jaarlijks",
        "lifetime": "Levenslang",
        "whatsNew": "Voegt 41 weergavetalen toe aan de app, Store-pagina, schermafbeeldingen, Pyonta+-tekst en toegankelijkheidsinformatie.",
        "nonAffiliation": "Pyonta is onafhankelijk en niet gelieerd aan Google of Apple.",
    },
    "pl": {
        "monthly": "Miesięcznie",
        "yearly": "Rocznie",
        "lifetime": "Dożywotnio",
        "whatsNew": "Dodaje 41 języków wyświetlania w aplikacji, stronie Store, zrzutach ekranu, tekście Pyonta+ i informacjach o dostępności.",
        "nonAffiliation": "Pyonta jest niezależna i nie jest powiązana z Google ani Apple.",
    },
    "pt-BR": {
        "monthly": "Mensal",
        "yearly": "Anual",
        "lifetime": "Vitalício",
        "whatsNew": "Adiciona 41 idiomas de exibição no app, página da Store, capturas, texto Pyonta+ e informações de acessibilidade.",
        "nonAffiliation": "Pyonta é independente e não é afiliado ao Google ou à Apple.",
    },
    "pt-PT": {
        "monthly": "Mensal",
        "yearly": "Anual",
        "lifetime": "Vitalício",
        "whatsNew": "Adiciona 41 idiomas de apresentação na app, página da Store, capturas, texto Pyonta+ e informações de acessibilidade.",
        "nonAffiliation": "Pyonta é independente e não está afiliado à Google ou à Apple.",
    },
    "ro": {
        "monthly": "Lunar",
        "yearly": "Anual",
        "lifetime": "Pe viață",
        "whatsNew": "Adaugă 41 de limbi de afișare în aplicație, pagina Store, capturi, textul Pyonta+ și informațiile de accesibilitate.",
        "nonAffiliation": "Pyonta este independent și nu este afiliat cu Google sau Apple.",
    },
    "ru": {
        "monthly": "Ежемесячно",
        "yearly": "Ежегодно",
        "lifetime": "Навсегда",
        "whatsNew": "Добавляет 41 язык отображения в приложение, страницу Store, скриншоты, текст Pyonta+ и сведения о доступности.",
        "nonAffiliation": "Pyonta является независимым приложением и не связана с Google или Apple.",
    },
    "sk": {
        "monthly": "Mesačne",
        "yearly": "Ročne",
        "lifetime": "Doživotne",
        "whatsNew": "Pridáva 41 jazyk zobrazenia v aplikácii, stránke Store, snímkach, texte Pyonta+ a informáciách o prístupnosti.",
        "nonAffiliation": "Pyonta je nezávislá a nie je prepojená so spoločnosťami Google ani Apple.",
    },
    "sl": {
        "monthly": "Mesečno",
        "yearly": "Letno",
        "lifetime": "Doživljenjsko",
        "whatsNew": "Doda 41 prikaznih jezikov v aplikaciji, strani Store, posnetkih zaslona, besedilu Pyonta+ in informacijah o dostopnosti.",
        "nonAffiliation": "Pyonta je neodvisna in ni povezana z Googlom ali Applom.",
    },
    "sr": {
        "monthly": "Месечно",
        "yearly": "Годишње",
        "lifetime": "Доживотно",
        "whatsNew": "Додаје 41 језик приказа у апликацији, Store страници, снимцима екрана, Pyonta+ тексту и информацијама о приступачности.",
        "nonAffiliation": "Pyonta је независна и није повезана са Google-ом или Apple-ом.",
    },
    "sv": {
        "monthly": "Månadsvis",
        "yearly": "Årligen",
        "lifetime": "Livstid",
        "whatsNew": "Lägger till 41 visningsspråk i appen, Store-sidan, skärmbilder, Pyonta+-text och tillgänglighetsinformation.",
        "nonAffiliation": "Pyonta är oberoende och inte kopplad till Google eller Apple.",
    },
    "th": {
        "monthly": "รายเดือน",
        "yearly": "รายปี",
        "lifetime": "ตลอดชีพ",
        "whatsNew": "เพิ่มภาษาที่แสดง 41 ภาษาในแอป หน้า Store ภาพหน้าจอ ข้อความ Pyonta+ และข้อมูลการช่วยการเข้าถึง",
        "nonAffiliation": "Pyonta เป็นแอปอิสระและไม่ได้เป็นพันธมิตรกับ Google หรือ Apple",
    },
    "tr": {
        "monthly": "Aylık",
        "yearly": "Yıllık",
        "lifetime": "Ömür boyu",
        "whatsNew": "Uygulama, Store sayfası, ekran görüntüleri, Pyonta+ metni ve erişilebilirlik bilgileri için 41 görüntüleme dili ekler.",
        "nonAffiliation": "Pyonta bağımsızdır ve Google ya da Apple ile bağlantılı değildir.",
    },
    "uk": {
        "monthly": "Щомісячно",
        "yearly": "Щорічно",
        "lifetime": "Назавжди",
        "whatsNew": "Додає 41 мову відображення в застосунку, сторінці Store, знімках екрана, тексті Pyonta+ та інформації про доступність.",
        "nonAffiliation": "Pyonta є незалежним застосунком і не пов'язана з Google або Apple.",
    },
    "vi": {
        "monthly": "Hàng tháng",
        "yearly": "Hàng năm",
        "lifetime": "Trọn đời",
        "whatsNew": "Thêm 41 ngôn ngữ hiển thị trong ứng dụng, trang Store, ảnh chụp màn hình, văn bản Pyonta+ và thông tin trợ năng.",
        "nonAffiliation": "Pyonta độc lập và không liên kết với Google hoặc Apple.",
    },
    "zh-Hans": {
        "monthly": "月度",
        "yearly": "年度",
        "lifetime": "终身",
        "whatsNew": "为应用、Store 页面、截图、Pyonta+ 文案和辅助功能信息新增 41 种显示语言。",
        "nonAffiliation": "Pyonta 是独立应用，与 Google 或 Apple 没有关联。",
    },
    "zh-Hant": {
        "monthly": "月度",
        "yearly": "年度",
        "lifetime": "永久",
        "whatsNew": "為 App、Store 頁面、截圖、Pyonta+ 文案和輔助使用資訊新增 41 種顯示語言。",
        "nonAffiliation": "Pyonta 是獨立 App，與 Google 或 Apple 沒有關聯。",
    },
}


def load_screenshot_copy() -> dict[str, dict[str, str]]:
    sys.path.insert(0, str(SCREENSHOT_SCRIPT.parent))
    spec = importlib.util.spec_from_file_location("next_release_screenshots", SCREENSHOT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {SCREENSHOT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    copy = getattr(module, "COPY")
    overrides = getattr(module, "BODY_COPY_OVERRIDES", {})
    merged: dict[str, dict[str, str]] = {}
    for locale, values in copy.items():
        row = dict(values)
        row.update(overrides.get(locale, {}))
        merged[locale] = row
    return merged


def load_xcstrings_values(path: Path) -> dict[str, dict[str, str]]:
    data = json.loads(path.read_text())
    values: dict[str, dict[str, str]] = {}
    for key, item in data.get("strings", {}).items():
        values[key] = {}
        for locale, localized in (item.get("localizations") or {}).items():
            value = localized.get("stringUnit", {}).get("value")
            if value:
                values[key][locale] = value
    return values


def localized_value(strings: dict[str, dict[str, str]], key: str, locale: str, fallback: str) -> str:
    return strings.get(key, {}).get(locale) or strings.get(key, {}).get("en") or fallback


def normalized_line(value: str) -> str:
    return " ".join(value.replace("\n", " ").split())


def make_keywords(locale: str, subtitle: str) -> str:
    tokens = ["android", "quick share", "mac", "pyonta"]
    for token in normalized_line(subtitle).replace("/", " ").split():
        cleaned = token.strip(" ,.;:()[]{}")
        if cleaned and cleaned.lower() not in {item.lower() for item in tokens}:
            tokens.append(cleaned)
    keywords = ",".join(tokens)
    return keywords[:100].rstrip(",")


def make_description(
    locale: str,
    copy: dict[str, str],
    strings: dict[str, dict[str, str]],
    terms: dict[str, str],
) -> str:
    first_message = localized_value(
        strings,
        "FirstLaunchNotice.Message",
        locale,
        "Click the Pyonta icon in the menu bar to send files, receive from Android, upgrade to Pyonta+, or quit.",
    )
    privacy_label = localized_value(strings, "PrivacyPolicy", locale, "Privacy Policy")
    terms_label = localized_value(strings, "TermsOfUse", locale, "Terms of Use")
    paragraphs = [
        first_message,
        copy["receiveBody"],
        copy["sendBody"],
        copy["qrBody"],
        copy["plusBody"],
        f"{privacy_label}: {PRIVACY_URL}",
        f"{terms_label}: {TERMS_URL}",
        terms["nonAffiliation"],
    ]
    return "\n\n".join(normalized_line(paragraph) for paragraph in paragraphs)


def build_package() -> dict[str, Any]:
    screenshot_copy = load_screenshot_copy()
    strings = load_xcstrings_values(LOCALIZABLE)
    expected = locale_codes()
    localizations: dict[str, Any] = {}
    for locale in expected:
        if locale not in screenshot_copy:
            raise RuntimeError(f"Missing screenshot copy for {locale}")
        if locale not in TERMS:
            raise RuntimeError(f"Missing store terms for {locale}")
        copy = screenshot_copy[locale]
        terms = TERMS[locale]
        subtitle = SUBTITLE_OVERRIDES.get(locale, copy["subtitle"])
        iap_description = IAP_SHORT_DESCRIPTIONS.get(locale, normalized_line(copy["plusBody"]))
        localizations[locale] = {
            "xcodeLocale": locale,
            "ascLocaleCandidate": ASC_LOCALE_CANDIDATES.get(locale, locale),
            "appStoreConnectMetadataSupported": locale not in ASC_METADATA_UNSUPPORTED_LOCALES,
            "displayGroup": next(item.display_group for item in TARGET_LOCALES if item.code == locale),
            "translationStatus": "llm-draft-needs-native-review",
            "appInfo": {
                "name": "Pyonta",
                "subtitle": subtitle,
                "privacyPolicyUrl": PRIVACY_URL,
            },
            "versionMetadata": {
                "description": make_description(locale, copy, strings, terms),
                "keywords": make_keywords(locale, subtitle),
                "promotionalText": normalized_line(copy["receiveBody"]),
                "supportUrl": SUPPORT_URL,
                "marketingUrl": MARKETING_URL,
                "whatsNew": terms["whatsNew"],
            },
            "iap": {
                "subscriptionGroup": {"referenceName": "Pyonta+"},
                "products": {
                    "monthly": {
                        "productId": "com.odiften.pyonta.plus.monthly",
                        "displayName": f"Pyonta+ {terms['monthly']}",
                        "description": iap_description,
                    },
                    "yearly": {
                        "productId": "com.odiften.pyonta.plus.yearly",
                        "displayName": f"Pyonta+ {terms['yearly']}",
                        "description": iap_description,
                    },
                    "lifetime": {
                        "productId": "com.odiften.pyonta.plus.lifetime",
                        "displayName": f"Pyonta+ {terms['lifetime']}",
                        "description": iap_description,
                    },
                },
            },
            "screenshots": {
                "directory": f"design/appstore-screenshots/next-release/{locale}",
                "files": list(EXPECTED_SCREENSHOT_FILES),
                "reviewScreenshot": f"design/appstore-screenshots/next-release/review/pyonta-plus-required-{locale}-2880x1800.png",
            },
        }
    return {
        "schemaVersion": 1,
        "app": {
            "name": "Pyonta",
            "appleId": "6774222545",
            "bundleId": "com.odiften.pyonta",
            "platform": "MAC_OS",
            "primaryLocale": "en-US",
        },
        "releasePackage": {
            "scope": "next App Store submission package",
            "targetVersion": "1.0.3",
            "targetBuild": "21",
            "localeIdCount": len(expected),
            "publicDisplayLanguageCount": display_language_count(),
            "sourceLocaleMatrix": "scripts/next_release_locales.py",
            "appStoreConnectMetadataLocaleIdCount": len(expected) - len(ASC_METADATA_UNSUPPORTED_LOCALES),
            "appStoreConnectMetadataUnsupportedLocaleIds": sorted(ASC_METADATA_UNSUPPORTED_LOCALES),
            "liveMutationPolicy": "read-only local draft; App Store Connect writes require user confirmation",
        },
        "liveStateReadback": {
            "checkedAtJST": "2026-06-24 09:54",
            "publicStorefrontVersion": "JP/US public App Store page, lookup, and search are visible; raw iTunes lookup still reports version 1.0.1/currentVersionReleaseDate 2026-06-22T00:14:12Z at 09:54 JST while App Store Connect has 1.0.2 READY_FOR_SALE.",
            "appStoreConnectVersion102": {
                "state": "READY_FOR_SALE",
                "reviewSubmissionState": "COMPLETE",
                "reviewItemStates": ["APPROVED"],
                "selectedBuild": "20",
            },
            "iapPriceSchedule": {
                "yearly": {
                    "JPN": {"customerPrice": "800", "starts": "2026-06-24"},
                    "USA": {"customerPrice": "4.99", "starts": "2026-06-24"},
                    "preserveExistingSubscriberPrice": True,
                },
                "lifetime": {
                    "JPN": {"customerPrice": "1200", "starts": "2026-06-24"},
                    "USA": {"customerPrice": "6.99", "starts": "2026-06-24", "automaticFromBaseTerritory": "JPN"},
                },
            },
        },
        "accessibilityDeclarations": {
            "localizationPolicy": "App Store accessibility feature labels are system-localized; this package applies the same declarations to every target locale.",
            "localeCoverage": expected,
            "appStoreConnect": {
                "deviceFamily": "MAC",
                "publish": True,
                "supportsDarkInterface": True,
                "supportsSufficientContrast": True,
                "supportsDifferentiateWithoutColorAlone": True,
                "supportsVoiceover": False,
                "supportsVoiceControl": False,
                "supportsReducedMotion": False,
                "supportsLargerText": False,
                "supportsCaptions": False,
                "supportsAudioDescriptions": False,
            },
            "claimedForSubmission": [
                {
                    "feature": "Dark Interface",
                    "attribute": "supportsDarkInterface",
                    "evidence": "User-facing surfaces use AppKit/SwiftUI menus, alerts, and system colors; screenshot readability was checked on full-size assets and contact sheets.",
                },
                {
                    "feature": "Sufficient Contrast",
                    "attribute": "supportsSufficientContrast",
                    "evidence": "Core app UI uses system label colors and native controls; localized screenshot text remains readable in full-size and thumbnail/contact-sheet review.",
                },
                {
                    "feature": "Differentiates Without Color",
                    "attribute": "supportsDifferentiateWithoutColorAlone",
                    "evidence": "Core states are expressed with text labels, menu titles, alerts, and notifications, not only color.",
                },
            ],
            "notClaimedForSubmission": [
                "VoiceOver",
                "Voice Control",
                "Reduced Motion",
                "Larger Text",
                "Captions",
                "Audio Descriptions",
            ],
        },
        "localizations": localizations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    package = build_package()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {output}")
    print(
        f"Locales: {package['releasePackage']['localeIdCount']} IDs / "
        f"{package['releasePackage']['publicDisplayLanguageCount']} display languages"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
