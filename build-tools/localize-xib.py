#!/usr/bin/env python3
"""Update XIB xcstrings files to cover all 18 locales.

Strategy: keep existing translations untouched (NearDrop / QuickDrop-derived
human translations from ar/ja/ko/nl/pt-PT/ro/ru/uk/zh-Hans) and only fill in
the 8 missing locales (de, es, fr, hu, it, pt-BR, th, zh-Hant) plus any
keys that originally had only en/ru.

Per PROJECT_INFO.md: ja/en are author-quality, the other 16 are LLM-quality
acceptable for Day-1 launch.

Run:
    python3 build-tools/localize-xib.py
"""
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHARE_XCSTRINGS = ROOT / "ShareExtension" / "mul.lproj" / "ShareViewController.xcstrings"
SEND_XCSTRINGS = ROOT / "Pyonta" / "mul.lproj" / "SendViewController.xcstrings"

ALL_LOCALES = [
    "ar", "de", "en", "es", "fr", "hu", "it", "ja", "ko", "nl",
    "pt-BR", "pt-PT", "ro", "ru", "th", "uk", "zh-Hans", "zh-Hant",
]

# Translations keyed by the source English string. Only fill locales that
# the existing xcstrings does not already provide. Existing values are kept.
TRANSLATIONS: dict[str, dict[str, str]] = {
    "Cancel": {
        "de": "Abbrechen",
        "es": "Cancelar",
        "fr": "Annuler",
        "hu": "Mégse",
        "it": "Annulla",
        "pt-BR": "Cancelar",
        "th": "ยกเลิก",
        "zh-Hant": "取消",
    },
    "Looking for devices...": {
        "de": "Geräte werden gesucht …",
        "es": "Buscando dispositivos…",
        "fr": "Recherche d’appareils…",
        "hu": "Eszközök keresése…",
        "it": "Ricerca dispositivi…",
        "pt-BR": "À procura de dispositivos…",
        "th": "กำลังค้นหาอุปกรณ์…",
        "zh-Hant": "正在尋找附近的裝置…",
    },
    "If you don't see your device, open \"Google Files\" app and tap \"Receive\" on the Nearby Share tab.": {
        "de": "Wenn dein Gerät nicht erscheint, öffne die App „Google Files“ und tippe im Tab „Nearby Share“ auf „Empfangen“.",
        "es": "Si no ves tu dispositivo, abre la app «Google Files» y toca «Recibir» en la pestaña Compartir con Nearby.",
        "fr": "Si votre appareil n’apparaît pas, ouvrez l’application « Google Files » et appuyez sur « Recevoir » dans l’onglet Partage à proximité.",
        "hu": "Ha nem látod a készülékedet, nyisd meg a „Google Files” alkalmazást, és koppints a „Fogadás” gombra a Megosztás a közelben fülön.",
        "it": "Se non vedi il tuo dispositivo, apri l’app «Google Files» e tocca «Ricevi» nella scheda Condivisione nelle vicinanze.",
        "pt-BR": "Se você não vê o seu dispositivo, abra o aplicativo \"Google Files\" e toque em \"Receber\" na aba Compartilhamento Próximo.",
        "th": "หากไม่พบอุปกรณ์ของคุณ ให้เปิดแอป \"Google Files\" แล้วแตะ \"รับ\" ในแท็บแชร์กับอุปกรณ์ใกล้เคียง",
        "zh-Hant": "如果看不到你的裝置，請開啟「Google Files」App，並在「附近分享」分頁點選「接收」。",
    },
    # Modernized "device not found" hint. Replaces the legacy "Google Files" tip
    # which predates Quick Share's OS integration on Android. We rewrite the
    # source text and force-update every locale (see REPLACE_BY_OBJECT_ID).
    "If your device doesn't appear, turn its screen on and set Quick Share to be visible to Everyone.": {
        "ar": "إذا لم يظهر جهازك، فعّل الشاشة واضبط مشاركة قريبة على الظهور للجميع.",
        "de": "Wenn dein Gerät nicht erscheint, schalte den Bildschirm ein und stelle Nearby Share auf „Für alle sichtbar“.",
        "es": "Si no aparece tu dispositivo, enciende su pantalla y configura Compartir cerca como visible para Todos.",
        "fr": "Si votre appareil n’apparaît pas, allumez son écran et réglez Partage à proximité sur « Visible par tous ».",
        "hu": "Ha az eszközöd nem jelenik meg, kapcsold be a képernyőjét, és állítsd a Megosztás a közelben láthatóságát „Mindenki” értékre.",
        "it": "Se il dispositivo non compare, accendi lo schermo e imposta Condivisione nelle vicinanze su «Visibile a tutti».",
        "ja": "デバイスが表示されない場合は、画面を ON にして、Quick Share の表示設定を「全員」にしてください。",
        "ko": "기기가 표시되지 않으면 화면을 켜고 Quick Share의 공개 범위를 ‘모든 사람’으로 설정하세요.",
        "nl": "Als je apparaat niet verschijnt, zet het scherm aan en stel Delen met apparaten in de buurt in op zichtbaar voor Iedereen.",
        "pt-BR": "Se o seu dispositivo não aparecer, ligue a tela e defina o Compartilhamento Próximo como visível para Todos.",
        "pt-PT": "Se o teu dispositivo não aparecer, liga o ecrã e define a Partilha Próxima como visível para Todos.",
        "ro": "Dacă dispozitivul nu apare, aprinde-i ecranul și setează Partajare în apropiere la „Vizibil pentru toți”.",
        "ru": "Если устройство не появляется, включите его экран и установите видимость Quick Share как «Всем».",
        "th": "หากไม่พบอุปกรณ์ ให้เปิดหน้าจอและตั้งค่าการแชร์กับอุปกรณ์ใกล้เคียงให้มองเห็นได้สำหรับทุกคน",
        "uk": "Якщо пристрій не зʼявляється, увімкніть його екран і встановіть для функції «Поділитися з пристроями поблизу» видимість «Усім».",
        "zh-Hans": "如果设备未显示，请点亮屏幕，并将“附近分享”可见性设置为“所有人”。",
        "zh-Hant": "若裝置未顯示，請點亮螢幕，並將「附近分享」可見性設為「所有人」。",
    },
    "Use QR code...": {
        "ar": "استخدام رمز QR...",
        "de": "QR-Code verwenden …",
        "es": "Usar código QR…",
        "fr": "Utiliser un QR code…",
        "hu": "QR-kód használata…",
        "it": "Usa codice QR…",
        "ja": "QR コードを使う…",
        "ko": "QR 코드 사용...",
        "nl": "QR-code gebruiken…",
        "pt-BR": "Usar código QR…",
        "pt-PT": "Usar código QR…",
        "ro": "Folosește cod QR…",
        "th": "ใช้ QR โค้ด…",
        "uk": "Використати QR-код…",
        "zh-Hans": "使用二维码…",
        "zh-Hant": "使用 QR 碼…",
    },
    "Scan this QR code with an Android device. The transfer will begin automatically.": {
        "ar": "امسح رمز QR هذا باستخدام جهاز Android. ستبدأ عملية النقل تلقائياً.",
        "de": "Scanne diesen QR-Code mit einem Android-Gerät. Die Übertragung beginnt automatisch.",
        "es": "Escanea este código QR con un dispositivo Android. La transferencia comenzará automáticamente.",
        "fr": "Scannez ce QR code avec un appareil Android. Le transfert démarrera automatiquement.",
        "hu": "Olvasd be ezt a QR-kódot egy Android-eszközzel. Az átvitel automatikusan elindul.",
        "it": "Scansiona questo codice QR con un dispositivo Android. Il trasferimento inizierà automaticamente.",
        "ja": "この QR コードを Android 端末で読み取ってください。転送が自動的に始まります。",
        "ko": "Android 기기로 이 QR 코드를 스캔하세요. 전송이 자동으로 시작됩니다.",
        "nl": "Scan deze QR-code met een Android-apparaat. De overdracht begint automatisch.",
        "pt-BR": "Escaneie este código QR com um dispositivo Android. A transferência começará automaticamente.",
        "pt-PT": "Lê este código QR com um dispositivo Android. A transferência começa automaticamente.",
        "ro": "Scanează acest cod QR cu un dispozitiv Android. Transferul va începe automat.",
        "th": "สแกน QR โค้ดนี้ด้วยอุปกรณ์ Android การถ่ายโอนจะเริ่มโดยอัตโนมัติ",
        "uk": "Відскануйте цей QR-код пристроєм Android. Передавання розпочнеться автоматично.",
        "zh-Hans": "用 Android 设备扫描此二维码，传输将自动开始。",
        "zh-Hant": "用 Android 裝置掃描此 QR 碼，傳輸將自動開始。",
    },
    "If this doesn't work, make sure that the device and your Mac are on the same network, and that the router isn't blocking LAN communication.": {
        "ar": "إذا لم ينجح ذلك، تأكد من أن الجهاز و Mac على نفس الشبكة، وأن جهاز التوجيه لا يحجب الاتصال داخل الشبكة المحلية.",
        "de": "Wenn es nicht funktioniert, stelle sicher, dass das Gerät und dein Mac im selben Netzwerk sind und dein Router die LAN-Kommunikation nicht blockiert.",
        "es": "Si no funciona, comprueba que el dispositivo y tu Mac estén en la misma red y que el router no esté bloqueando la comunicación LAN.",
        "fr": "Si cela ne fonctionne pas, vérifiez que l’appareil et votre Mac sont sur le même réseau et que le routeur ne bloque pas la communication LAN.",
        "hu": "Ha nem működik, ellenőrizd, hogy az eszköz és a Maced ugyanazon a hálózaton van-e, és hogy a router nem blokkolja-e a LAN-kommunikációt.",
        "it": "Se non funziona, verifica che il dispositivo e il tuo Mac siano sulla stessa rete e che il router non blocchi la comunicazione LAN.",
        "ja": "うまくいかない場合は、Android 端末と Mac が同じネットワークに接続されていること、ルーターが LAN 内通信をブロックしていないことを確認してください。",
        "ko": "작동하지 않는 경우, 기기와 Mac이 같은 네트워크에 연결되어 있고 공유기가 LAN 통신을 차단하지 않는지 확인하세요.",
        "nl": "Werkt het niet? Controleer of het apparaat en je Mac op hetzelfde netwerk zijn, en of de router het LAN-verkeer niet blokkeert.",
        "pt-BR": "Se não funcionar, confirme que o dispositivo e o seu Mac estão na mesma rede e que o roteador não está bloqueando a comunicação na LAN.",
        "pt-PT": "Se não funcionar, certifica-te de que o dispositivo e o teu Mac estão na mesma rede e que o router não está a bloquear a comunicação na LAN.",
        "ro": "Dacă nu funcționează, asigură-te că dispozitivul și Mac-ul sunt în aceeași rețea și că routerul nu blochează comunicarea în LAN.",
        "th": "หากไม่ได้ผล โปรดตรวจสอบว่าอุปกรณ์และ Mac อยู่ในเครือข่ายเดียวกัน และเราเตอร์ไม่ได้บล็อกการสื่อสารใน LAN",
        "uk": "Якщо не працює, переконайтесь, що пристрій і Mac у тій самій мережі, а маршрутизатор не блокує обмін у локальній мережі.",
        "zh-Hans": "如无法连接，请确认设备和 Mac 在同一网络中，并确保路由器没有阻止局域网通信。",
        "zh-Hant": "若無法連線，請確認裝置與 Mac 位於同一網路，且路由器沒有阻擋區域網路通訊。",
    },
}


# Object IDs whose source English string we want to *replace* (not just fill).
# Use this when modernizing legacy NearDrop/QuickDrop text. The new English
# value also has to be present as a key in TRANSLATIONS so non-English locales
# can be regenerated.
REPLACE_BY_OBJECT_ID: dict[str, str] = {
    # Legacy: 'If you don\'t see your device, open "Google Files" app and tap "Receive" on the Nearby Share tab.'
    "vla-gF-eJo.title": "If your device doesn't appear, turn its screen on and set Quick Share to be visible to Everyone.",
}


def english_value(key_data: dict) -> str | None:
    en = key_data.get("localizations", {}).get("en", {}).get("stringUnit", {}).get("value")
    if en is not None:
        return en
    # Fall back to the "comment" field which contains 'title = "..."'
    comment = key_data.get("comment", "")
    marker = 'title = "'
    if marker in comment:
        start = comment.index(marker) + len(marker)
        end = comment.index('"', start) if '"' in comment[start:] else None
        if end is not None:
            return comment[start:end]
    return None


def needs_locale(key_data: dict, locale: str) -> bool:
    locs = key_data.setdefault("localizations", OrderedDict())
    if locale in locs:
        existing = locs[locale].get("stringUnit", {}).get("value")
        return existing is None or existing == ""
    return True


def set_translation(key_data: dict, locale: str, value: str, *, state: str = "translated") -> None:
    locs = key_data.setdefault("localizations", OrderedDict())
    locs[locale] = OrderedDict([
        ("stringUnit", OrderedDict([
            ("state", state),
            ("value", value),
        ])),
    ])


def update_xcstrings(path: Path, *, app_name_key: str | None) -> None:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f, object_pairs_hook=OrderedDict)

    for key, key_data in data["strings"].items():
        # App-name key: don't translate, mirror "Pyonta" in every locale.
        if app_name_key and key == app_name_key:
            for loc in ALL_LOCALES:
                if needs_locale(key_data, loc):
                    state = "new" if loc == "en" else "translated"
                    set_translation(key_data, loc, "Pyonta", state=state)
            continue

        # Force-replace mode: rewrite source English + every locale.
        if key in REPLACE_BY_OBJECT_ID:
            new_en = REPLACE_BY_OBJECT_ID[key]
            translations = TRANSLATIONS.get(new_en, {})
            # Replace the comment so Xcode shows the current source string.
            old_comment = key_data.get("comment", "")
            if 'title = "' in old_comment:
                head, _, tail = old_comment.partition('title = "')
                _, _, after = tail.partition('"')
                key_data["comment"] = f'{head}title = "{new_en}"{after}'
            set_translation(key_data, "en", new_en, state="new")
            for loc in ALL_LOCALES:
                if loc == "en":
                    continue
                value = translations.get(loc)
                if value is None:
                    continue
                set_translation(key_data, loc, value)
            continue

        en_val = english_value(key_data)
        if en_val is None:
            continue

        # Always make sure "en" is present (source).
        if needs_locale(key_data, "en"):
            set_translation(key_data, "en", en_val, state="new")

        translations = TRANSLATIONS.get(en_val, {})
        for loc in ALL_LOCALES:
            if loc == "en":
                continue
            if not needs_locale(key_data, loc):
                continue
            value = translations.get(loc)
            if value is None:
                continue  # leave missing locales as-is if we don't have a translation yet
            set_translation(key_data, loc, value)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Updated {path}")


def create_send_xcstrings_from_share(share_path: Path, send_path: Path) -> None:
    """Generate Pyonta target's SendViewController.xcstrings from ShareExtension's.

    The XIBs share identical ObjectIDs, so the same xcstrings content works for
    both. We re-derive Send from the freshly-updated Share so the two stay in
    lock-step.
    """
    with share_path.open("r", encoding="utf-8") as f:
        data = json.load(f, object_pairs_hook=OrderedDict)
    send_path.parent.mkdir(parents=True, exist_ok=True)
    with send_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Wrote {send_path}")


if __name__ == "__main__":
    # Step 1: extend ShareViewController.xcstrings to all 18 locales.
    update_xcstrings(SHARE_XCSTRINGS, app_name_key="0xp-rC-2gr.title")
    # Step 2: clone result into Pyonta target.
    create_send_xcstrings_from_share(SHARE_XCSTRINGS, SEND_XCSTRINGS)
