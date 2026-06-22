#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import random
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "design" / "appstore-screenshots"
ICON = ROOT / "design" / "appicon-master.png"
STRINGS = ROOT / "Pyonta" / "Localizable.xcstrings"

W, H = 2880, 1800

INK = "#18202A"
MUTED = "#58636F"
BLUE = "#176B87"
GREEN = "#56A95D"
AMBER = "#E6A33A"
RED = "#E06C75"
PANEL = "#FFFFFF"
LINE = "#D7DEE5"
BG = "#F4F6F3"
BG2 = "#EEF6F8"


def find_font(name_part: str, fallback: str) -> Path:
    for base in (Path("/System/Library/Fonts"), Path("/Library/Fonts")):
        for path in base.glob("*"):
            if name_part in path.name:
                return path
    return Path(fallback)


FONT_REG = find_font("ヒラギノ角ゴシック W4", "/System/Library/Fonts/HelveticaNeue.ttc")
FONT_BOLD = find_font("ヒラギノ角ゴシック W8", "/System/Library/Fonts/HelveticaNeue.ttc")
FONT_MED = find_font("ヒラギノ角ゴシック W6", "/System/Library/Fonts/HelveticaNeue.ttc")
CJK_REG = Path("/Library/Fonts/RODE Noto Sans CJK SC R.otf")
CJK_BOLD = Path("/Library/Fonts/RODE Noto Sans CJK SC B.otf")
if CJK_REG.exists() and CJK_BOLD.exists():
    FONT_REG = CJK_REG
    FONT_BOLD = CJK_BOLD
    FONT_MED = CJK_BOLD

LOCALES = ("en", "ja", "de", "fr", "es", "it", "ko", "zh-Hans", "zh-Hant", "pt-BR")
XCODE_LOCALES = {"en": "en", "de": "de", "fr": "fr", "es": "es", "it": "it", "pt-BR": "pt-BR"}

SUBTITLES = {
    "en": "Android file transfer utility",
    "ja": "Androidファイル転送",
    "de": "Android-Dateitransfer",
    "fr": "Transfert de fichiers Android",
    "es": "Transferencia de archivos Android",
    "it": "Trasferimento file Android",
    "ko": "Android 파일 전송",
    "zh-Hans": "Android 文件传输",
    "zh-Hant": "Android 檔案傳輸",
    "pt-BR": "Transferência de arquivos Android",
}

SCREENSHOT_TEXT = {
    "receiveTitle": {
        "en": "Easy Android-to-Mac transfer",
        "ja": "Android から Mac へかんたん転送",
        "de": "Android zu Mac einfach übertragen",
        "fr": "Transfert Android vers Mac facile",
        "es": "Transferencia fácil de Android a Mac",
        "it": "Trasferisci da Android a Mac",
        "ko": "Android에서 Mac으로 간편 전송",
        "zh-Hans": "轻松从 Android 传到 Mac",
        "zh-Hant": "輕鬆從 Android 傳到 Mac",
        "pt-BR": "Transferência fácil do Android para Mac",
    },
    "receiveBody": {
        "en": "Send from Android's share sheet. Receive photos, videos, PDFs, links, and text on your Mac.",
        "ja": "Androidの共有から送るだけ。写真・動画・PDF・リンク・テキストをMacで受け取れます。",
        "de": "Aus dem Android-Teilen-Menü senden. Fotos, Videos, PDFs, Links und Text auf dem Mac empfangen.",
        "fr": "Envoyez depuis le menu Partager d'Android. Recevez photos, vidéos, PDF, liens et texte sur votre Mac.",
        "es": "Envía desde el menú Compartir de Android. Recibe fotos, videos, PDF, enlaces y texto en tu Mac.",
        "it": "Invia dal menu Condividi di Android. Ricevi foto, video, PDF, link e testo sul tuo Mac.",
        "ko": "Android 공유 메뉴에서 보내면 사진, 동영상, PDF, 링크, 텍스트를 Mac에서 받을 수 있습니다.",
        "zh-Hans": "从 Android 分享菜单发送。在 Mac 上接收照片、视频、PDF、链接和文本。",
        "zh-Hant": "從 Android 分享選單傳送。在 Mac 上接收照片、影片、PDF、連結和文字。",
        "pt-BR": "Envie pelo menu Compartilhar do Android. Receba fotos, vídeos, PDFs, links e texto no Mac.",
    },
    "sendTitle": {
        "en": "Send files and clipboard back",
        "ja": "Mac から Android へも送れる",
        "de": "Dateien und Zwischenablage senden",
        "fr": "Envoyez fichiers et presse-papiers",
        "es": "Envía archivos y portapapeles",
        "it": "Invia file e appunti",
        "ko": "파일과 클립보드도 보내기",
        "zh-Hans": "也能发送文件和剪贴板",
        "zh-Hant": "也能傳送檔案和剪貼簿",
        "pt-BR": "Envie arquivos e área de transferência",
    },
    "sendBody": {
        "en": "Use the menu bar or Finder's Share sheet to send files, selected content, or clipboard text to a nearby Android device.",
        "ja": "メニューバーやFinderの共有から、ファイルやクリップボードの内容を近くのAndroid端末へ送信できます。",
        "de": "Sende Dateien, ausgewählte Inhalte oder Text aus der Zwischenablage über Menüleiste oder Finder an Android.",
        "fr": "Utilisez la barre de menus ou le partage du Finder pour envoyer fichiers, contenu sélectionné ou texte vers Android.",
        "es": "Usa la barra de menús o Compartir en Finder para enviar archivos, contenido seleccionado o texto a Android.",
        "it": "Usa la barra dei menu o Condividi nel Finder per inviare file, contenuti selezionati o testo ad Android.",
        "ko": "메뉴 막대나 Finder 공유에서 파일, 선택한 콘텐츠, 클립보드 텍스트를 가까운 Android로 보냅니다.",
        "zh-Hans": "通过菜单栏或 Finder 分享，将文件、所选内容或剪贴板文本发送到附近的 Android。",
        "zh-Hant": "透過選單列或 Finder 分享，將檔案、所選內容或剪貼簿文字傳送到附近的 Android。",
        "pt-BR": "Use a barra de menus ou o Compartilhar do Finder para enviar arquivos, conteúdo selecionado ou texto ao Android.",
    },
    "qrTitle": {
        "en": "QR fallback when devices do not appear",
        "ja": "見つからない時は QR でフォールバック",
        "de": "QR-Fallback, wenn Geräte fehlen",
        "fr": "QR de secours si aucun appareil n'apparaît",
        "es": "QR de respaldo si no aparecen dispositivos",
        "it": "QR di riserva se i dispositivi non appaiono",
        "ko": "기기가 보이지 않을 때 QR로 연결",
        "zh-Hans": "设备未出现时可用 QR 继续",
        "zh-Hant": "裝置未出現時可用 QR 繼續",
        "pt-BR": "QR de reserva quando dispositivos não aparecem",
    },
    "qrBody": {
        "en": "If discovery is blocked by Wi-Fi settings or Android visibility, Pyonta can show a QR code and keep the transfer moving.",
        "ja": "Wi-Fi設定やAndroid側の公開状態で見つからない時も、QRコード経由で転送を続けられます。",
        "de": "Wenn WLAN-Einstellungen oder Android-Sichtbarkeit stören, zeigt Pyonta einen QR-Code zum Fortsetzen.",
        "fr": "Si le Wi-Fi ou la visibilité Android bloque la détection, Pyonta affiche un QR code pour continuer.",
        "es": "Si el Wi-Fi o la visibilidad de Android bloquean la detección, Pyonta muestra un código QR para continuar.",
        "it": "Se Wi-Fi o visibilità Android bloccano il rilevamento, Pyonta mostra un codice QR per continuare.",
        "ko": "Wi-Fi 설정이나 Android 공개 상태 때문에 찾지 못해도 QR 코드로 전송을 이어갈 수 있습니다.",
        "zh-Hans": "如果 Wi-Fi 设置或 Android 可见性阻止发现，Pyonta 可显示 QR 码继续传输。",
        "zh-Hant": "如果 Wi-Fi 設定或 Android 可見性阻止尋找，Pyonta 可顯示 QR 碼繼續傳輸。",
        "pt-BR": "Se o Wi-Fi ou a visibilidade do Android bloquear a busca, Pyonta mostra um QR Code para continuar.",
    },
    "qrHeading": {
        "en": "Scan this QR code",
        "ja": "QRコードをスキャン",
        "de": "Diesen QR-Code scannen",
        "fr": "Scannez ce QR code",
        "es": "Escanea este código QR",
        "it": "Scansiona questo codice QR",
        "ko": "이 QR 코드를 스캔",
        "zh-Hans": "扫描此 QR 码",
        "zh-Hant": "掃描此 QR 碼",
        "pt-BR": "Escaneie este QR Code",
    },
    "qrDesc": {
        "en": "The transfer begins automatically after scanning.",
        "ja": "スキャンすると転送が自動で始まります。",
        "de": "Die Übertragung startet nach dem Scannen automatisch.",
        "fr": "Le transfert démarre automatiquement après le scan.",
        "es": "La transferencia comienza automáticamente al escanear.",
        "it": "Il trasferimento inizia automaticamente dopo la scansione.",
        "ko": "스캔하면 전송이 자동으로 시작됩니다.",
        "zh-Hans": "扫描后会自动开始传输。",
        "zh-Hant": "掃描後會自動開始傳輸。",
        "pt-BR": "A transferência começa automaticamente após a leitura.",
    },
    "plusTitle": {
        "en": "Unlock receiving with Pyonta+",
        "ja": "Androidからの受信を\nPyonta+ で解放",
        "de": "Empfang mit Pyonta+ freischalten",
        "fr": "Débloquez la réception avec Pyonta+",
        "es": "Desbloquea la recepción con Pyonta+",
        "it": "Sblocca la ricezione con Pyonta+",
        "ko": "Pyonta+로 받기 기능 잠금 해제",
        "zh-Hans": "用 Pyonta+ 解锁接收",
        "zh-Hant": "用 Pyonta+ 解鎖接收",
        "pt-BR": "Desbloqueie o recebimento com Pyonta+",
    },
    "plusBody": {
        "en": "Sending from your Mac stays free. Pyonta+ unlocks the main Android-to-Mac receiving flow that saves time every day.",
        "ja": "Macからの送信は無料のまま。毎日使うAndroidからMacへの受信をPyonta+で解放します。",
        "de": "Senden vom Mac bleibt kostenlos. Pyonta+ schaltet den täglichen Android-zu-Mac-Empfang frei.",
        "fr": "L'envoi depuis le Mac reste gratuit. Pyonta+ débloque la réception Android vers Mac du quotidien.",
        "es": "Enviar desde tu Mac sigue gratis. Pyonta+ desbloquea la recepción de Android a Mac para uso diario.",
        "it": "L'invio dal Mac resta gratuito. Pyonta+ sblocca la ricezione Android-Mac per l'uso quotidiano.",
        "ko": "Mac에서 보내기는 무료입니다. Pyonta+는 매일 쓰는 Android에서 Mac으로 받기 흐름을 열어줍니다.",
        "zh-Hans": "从 Mac 发送仍然免费。Pyonta+ 解锁日常使用的 Android 到 Mac 接收流程。",
        "zh-Hant": "從 Mac 傳送仍然免費。Pyonta+ 解鎖日常使用的 Android 到 Mac 接收流程。",
        "pt-BR": "Enviar do Mac continua grátis. Pyonta+ desbloqueia o recebimento Android para Mac no dia a dia.",
    },
}

BUTTON_TEXT = {
    "cancel": {
        "en": "Cancel",
        "ja": "キャンセル",
        "de": "Abbrechen",
        "fr": "Annuler",
        "es": "Cancelar",
        "it": "Annulla",
        "ko": "취소",
        "zh-Hans": "取消",
        "zh-Hant": "取消",
        "pt-BR": "Cancelar",
    },
    "useQr": {
        "en": "Use QR code...",
        "ja": "QRコードを使用...",
        "de": "QR-Code verwenden...",
        "fr": "Utiliser un QR code...",
        "es": "Usar código QR...",
        "it": "Usa codice QR...",
        "ko": "QR 코드 사용...",
        "zh-Hans": "使用 QR 码...",
        "zh-Hant": "使用 QR 碼...",
        "pt-BR": "Usar QR Code...",
    },
}

PLUS_CHIPS = {
    "en": ["Monthly", "Yearly trial", "Lifetime"],
    "ja": ["月額", "年額トライアル", "買い切り"],
    "de": ["Monatlich", "Jahrestest", "Einmalig"],
    "fr": ["Mensuel", "Essai annuel", "À vie"],
    "es": ["Mensual", "Prueba anual", "De por vida"],
    "it": ["Mensile", "Prova annuale", "A vita"],
    "ko": ["월간", "연간 체험", "평생"],
    "zh-Hans": ["月度", "年度试用", "永久"],
    "zh-Hant": ["月付", "年度試用", "永久"],
    "pt-BR": ["Mensal", "Teste anual", "Vitalício"],
}


def font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    path = {"bold": FONT_BOLD, "medium": FONT_MED}.get(weight, FONT_REG)
    return ImageFont.truetype(str(path), size)


with STRINGS.open() as f:
    CATALOG = json.load(f)["strings"]


def tr(key: str, locale: str, default: str) -> str:
    item = CATALOG.get(key, {})
    catalog_locale = XCODE_LOCALES.get(locale, locale)
    unit = item.get("localizations", {}).get(catalog_locale, {}).get("stringUnit")
    return unit["value"] if unit else default


def rgba(hex_color: str, alpha: int) -> tuple[int, int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def shadow(base: Image.Image, rect: tuple[int, int, int, int], radius: int = 36, alpha: int = 45) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x1, y1, x2, y2 = rect
    d.rounded_rectangle((x1, y1 + 16, x2, y2 + 22), radius=radius, fill=(0, 0, 0, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(28))
    base.alpha_composite(layer)


def rounded(draw: ImageDraw.ImageDraw, rect, radius=36, fill=PANEL, outline=None, width=2):
    draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=outline, width=width)


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    no_line_start = "、。，．）」』】!?！？:：;；"
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        units = re.findall(r"[A-Za-z0-9+./-]+|[ァ-ヶー]+|[ぁ-ん]+|[一-龯々]+|\s+|.", paragraph)
        current = ""
        for unit in units:
            if unit.isspace() and not current:
                continue
            candidate = current + unit
            if text_size(draw, candidate, fnt)[0] <= max_width or not current:
                current = candidate
            elif unit in no_line_start:
                current += unit
            else:
                lines.append(current.rstrip())
                current = "" if unit.isspace() else unit.lstrip()
        if current:
            lines.append(current.rstrip())
    return lines


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill: str,
    max_width: int,
    line_gap: int = 16,
) -> int:
    x, y = xy
    for line in wrap(draw, text, fnt, max_width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += text_size(draw, line or "A", fnt)[1] + line_gap
    return y


def center_text(draw, rect, text, fnt, fill):
    x1, y1, x2, y2 = rect
    tw, th = text_size(draw, text, fnt)
    draw.text((x1 + (x2 - x1 - tw) / 2, y1 + (y2 - y1 - th) / 2 - 2), text, font=fnt, fill=fill)


def app_icon(size: int) -> Image.Image:
    icon = Image.open(ICON).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle((0, 0, size, size), radius=max(12, int(size * 0.18)), fill=255)
    icon.putalpha(mask)
    return icon


def base(locale: str, title: str, body: str, accent: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, H), fill=BG)
    d.ellipse((-260, -220, 720, 680), fill=rgba(BG2, 255))
    d.ellipse((2150, 1210, 3240, 2220), fill=rgba("#EDF4EA", 255))

    img.alpha_composite(app_icon(170), (190, 170))
    d.text((385, 196), "Pyonta", font=font(64, "bold"), fill=INK)
    subtitle = SUBTITLES[locale]
    d.text((388, 280), subtitle, font=font(34, "medium"), fill=MUTED)

    d.rounded_rectangle((190, 410, 330, 462), radius=26, fill=accent)
    d.text((214, 421), "macOS", font=font(26, "bold"), fill="white")
    title_bottom = draw_text(d, (190, 530), title, font(92, "bold"), INK, 910, 20)
    body_y = max(820, title_bottom + 34)
    draw_text(d, (194, body_y), body, font(40, "regular"), MUTED, 830, 18)
    return img, d


def draw_mac_window(img: Image.Image, rect, title: str = "") -> ImageDraw.ImageDraw:
    d = ImageDraw.Draw(img)
    shadow(img, rect, 38, 40)
    rounded(d, rect, 38, PANEL, LINE, 2)
    x1, y1, x2, y2 = rect
    d.rounded_rectangle((x1, y1, x2, y1 + 92), radius=38, fill="#F7F8FA")
    d.rectangle((x1, y1 + 46, x2, y1 + 92), fill="#F7F8FA")
    for i, c in enumerate((RED, AMBER, GREEN)):
        d.ellipse((x1 + 42 + i * 44, y1 + 34, x1 + 66 + i * 44, y1 + 58), fill=c)
    if title:
        center_text(d, (x1, y1 + 24, x2, y1 + 70), title, font(28, "medium"), MUTED)
    return d


def draw_menu_panel(img: Image.Image, rect, locale: str) -> None:
    d = ImageDraw.Draw(img)
    shadow(img, rect, 34, 38)
    rounded(d, rect, 34, PANEL, "#DCE3EA", 2)
    x1, y1, x2, _ = rect
    y = y1 + 44
    items = [
        (tr("VisibleToEveryone", locale, "Visible to everyone"), True),
        (tr("AutoAcceptFiles", locale, "Receive without asking"), True),
        (tr("OpenReceivedURLs", locale, "Open URLs automatically"), False),
        (tr("LaunchAtLogin", locale, "Launch at login"), True),
    ]
    for label, on in items:
        d.text((x1 + 46, y + 7), label, font=font(30, "medium"), fill=INK)
        toggle_x = x2 - 126
        fill = GREEN if on else "#C9D1D9"
        d.rounded_rectangle((toggle_x, y, toggle_x + 74, y + 38), radius=19, fill=fill)
        knob_x = toggle_x + (40 if on else 4)
        d.ellipse((knob_x, y + 4, knob_x + 30, y + 34), fill="white")
        y += 68
    d.line((x1 + 30, y + 6, x2 - 30, y + 6), fill=LINE, width=2)
    y += 32
    for label in (
        tr("SendFiles", locale, "Send files…"),
        tr("SendClipboard", locale, "Send clipboard…"),
        tr("PlusStatusInactive", locale, "Pyonta+: Inactive"),
    ):
        d.text((x1 + 46, y), label, font=font(30, "medium"), fill=INK)
        y += 58


def draw_phone(d: ImageDraw.ImageDraw, rect, label: str = "Android") -> None:
    x1, y1, x2, y2 = rect
    d.rounded_rectangle(rect, radius=58, fill="#202832")
    d.rounded_rectangle((x1 + 22, y1 + 28, x2 - 22, y2 - 28), radius=40, fill="#F8FAFC")
    d.rounded_rectangle((x1 + 88, y1 + 18, x2 - 88, y1 + 30), radius=6, fill="#11161C")
    d.text((x1 + 64, y1 + 90), label, font=font(30, "bold"), fill=INK)
    colors = (BLUE, GREEN, AMBER)
    for i in range(3):
        y = y1 + 178 + i * 86
        d.rounded_rectangle((x1 + 64, y, x2 - 64, y + 52), radius=18, fill="#E9EEF2")
        d.ellipse((x1 + 84, y + 13, x1 + 110, y + 39), fill=colors[i])
        d.rectangle((x1 + 128, y + 18, x2 - 92, y + 26), fill="#C5CFD8")
        d.rectangle((x1 + 128, y + 34, x2 - 140, y + 40), fill="#D8E0E7")


def draw_arrow(d: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str) -> None:
    d.line((start, end), fill=color, width=18)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 42
    p1 = (end[0] - size * math.cos(angle - 0.55), end[1] - size * math.sin(angle - 0.55))
    p2 = (end[0] - size * math.cos(angle + 0.55), end[1] - size * math.sin(angle + 0.55))
    d.polygon((end, p1, p2), fill=color)


def qr_pattern(size: int = 360) -> Image.Image:
    rng = random.Random(42)
    modules = 29
    pad = 4
    cell = size // (modules + pad * 2)
    img = Image.new("RGBA", (size, size), "white")
    d = ImageDraw.Draw(img)

    def finder(cx: int, cy: int):
        x = (cx + pad) * cell
        y = (cy + pad) * cell
        d.rectangle((x, y, x + 7 * cell, y + 7 * cell), fill=INK)
        d.rectangle((x + cell, y + cell, x + 6 * cell, y + 6 * cell), fill="white")
        d.rectangle((x + 2 * cell, y + 2 * cell, x + 5 * cell, y + 5 * cell), fill=INK)

    finder(0, 0)
    finder(modules - 7, 0)
    finder(0, modules - 7)
    for yy in range(modules):
        for xx in range(modules):
            if (xx < 8 and yy < 8) or (xx >= modules - 8 and yy < 8) or (xx < 8 and yy >= modules - 8):
                continue
            if rng.random() > 0.57:
                x = (xx + pad) * cell
                y = (yy + pad) * cell
                d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=INK)
    return img


def screenshot_receive(locale: str) -> None:
    title = SCREENSHOT_TEXT["receiveTitle"][locale]
    body = SCREENSHOT_TEXT["receiveBody"][locale]
    img, d = base(locale, title, body, BLUE)
    draw_mac_window(img, (1200, 270, 2590, 1380), "Pyonta")
    d.rectangle((1242, 392, 2548, 1290), fill="#F2F6F8")
    d.text((1330, 480), "MacBook Pro", font=font(60, "bold"), fill=INK)
    d.text((1334, 565), "Downloads", font=font(34, "medium"), fill=MUTED)
    draw_menu_panel(img, (1580, 340, 2450, 920), locale)
    draw_phone(d, (1080, 760, 1380, 1320))
    draw_arrow(d, (1390, 1010), (1560, 850), GREEN)
    d.rounded_rectangle((1326, 1165, 2032, 1248), radius=28, fill="#FFFFFF", outline=LINE, width=2)
    d.ellipse((1362, 1189, 1408, 1235), fill=GREEN)
    d.text((1435, 1187), "IMG_2042.jpg", font=font(34, "medium"), fill=INK)
    save(img, locale, "01-receive-from-android")


def screenshot_send(locale: str) -> None:
    title = SCREENSHOT_TEXT["sendTitle"][locale]
    body = SCREENSHOT_TEXT["sendBody"][locale]
    img, d = base(locale, title, body, GREEN)
    draw_mac_window(img, (1160, 300, 2470, 1300), tr("SendFiles.Title", locale, "Send files"))
    d.text((1270, 455), tr("SendFiles", locale, "Send files…"), font=font(58, "bold"), fill=INK)
    d.text((1274, 535), tr("SendClipboard", locale, "Send clipboard…"), font=font(36, "medium"), fill=MUTED)
    devices = [("Pixel 8 Pro", GREEN), ("Android device", BLUE)]
    for i, (name, color) in enumerate(devices):
        y = 665 + i * 138
        d.rounded_rectangle((1270, y, 2260, y + 102), radius=30, fill="#F7FAFB", outline=LINE, width=2)
        d.ellipse((1305, y + 27, 1353, y + 75), fill=color)
        d.text((1390, y + 27), name, font=font(40, "medium"), fill=INK)
        d.text((2105, y + 27), ">", font=font(42, "bold"), fill="#9DA8B3")
    d.rounded_rectangle((1270, 1030, 1788, 1112), radius=28, fill="#FFFFFF", outline=LINE, width=2)
    d.text((1326, 1050), BUTTON_TEXT["useQr"][locale], font=font(32, "medium"), fill=BLUE)
    draw_phone(d, (2290, 770, 2590, 1330))
    draw_arrow(d, (2030, 1110), (2270, 1060), GREEN)
    save(img, locale, "02-send-to-android")


def screenshot_qr(locale: str) -> None:
    title = SCREENSHOT_TEXT["qrTitle"][locale]
    body = SCREENSHOT_TEXT["qrBody"][locale]
    img, d = base(locale, title, body, AMBER)
    draw_mac_window(img, (1160, 270, 2470, 1370), "Pyonta")
    d.text((1390, 460), SCREENSHOT_TEXT["qrHeading"][locale], font=font(58, "bold"), fill=INK)
    qr = qr_pattern(450)
    shadow(img, (1580, 570, 2030, 1020), 22, 18)
    img.alpha_composite(qr, (1580, 570))
    desc = SCREENSHOT_TEXT["qrDesc"][locale]
    draw_text(d, (1394, 1080), desc, font(36, "regular"), MUTED, 760, 12)
    draw_phone(d, (2240, 650, 2540, 1210))
    d.rounded_rectangle((2314, 806, 2466, 958), radius=22, outline=BLUE, width=10)
    draw_arrow(d, (2190, 890), (2044, 800), AMBER)
    save(img, locale, "03-qr-fallback")


def draw_plus_alert(img: Image.Image, locale: str, rect) -> None:
    d = ImageDraw.Draw(img)
    shadow(img, rect, 36, 55)
    rounded(d, rect, 36, PANEL, "#CCD6DE", 2)
    x1, y1, x2, _ = rect
    img.alpha_composite(app_icon(110), (x1 + 60, y1 + 58))
    title_font = font(46 if locale in ("en", "ja") else 38, "bold")
    title_bottom = draw_text(
        d,
        (x1 + 200, y1 + 50),
        tr("UpgradeToPlus.Title", locale, "Upgrade to Pyonta+"),
        title_font,
        INK,
        x2 - x1 - 260,
        4,
    )
    msg = tr(
        "PlusRequired.Message",
        locale,
        "Receiving from Android requires Pyonta+. Upgrade, then ask the sender to try again.",
    )
    msg_font = font(26 if locale in ("ja", "ko", "zh-Hans", "zh-Hant") else 28, "regular")
    draw_text(d, (x1 + 200, max(y1 + 128, title_bottom + 8)), msg, msg_font, MUTED, x2 - x1 - 285, 10)
    cancel = BUTTON_TEXT["cancel"][locale]
    d.rounded_rectangle((x2 - 415, y1 + 310, x2 - 245, y1 + 370), radius=18, fill="#EEF3F7", outline=LINE)
    center_text(d, (x2 - 415, y1 + 310, x2 - 245, y1 + 370), cancel, font(26, "medium"), INK)
    d.rounded_rectangle((x2 - 225, y1 + 310, x2 - 50, y1 + 370), radius=18, fill=BLUE)
    center_text(d, (x2 - 225, y1 + 310, x2 - 50, y1 + 370), "OK", font(26, "bold"), "white")


def screenshot_plus(locale: str) -> None:
    title = SCREENSHOT_TEXT["plusTitle"][locale]
    body = SCREENSHOT_TEXT["plusBody"][locale]
    img, d = base(locale, title, body, BLUE)
    draw_mac_window(img, (1160, 330, 2500, 1330), "Pyonta")
    d.rectangle((1202, 452, 2458, 1240), fill="#F3F6F8")
    draw_plus_alert(img, locale, (1300, 610, 2400, 1040))
    chips = PLUS_CHIPS[locale]
    x = 1260
    for i, chip in enumerate(chips):
        w = [220, 300, 240][i]
        d.rounded_rectangle((x, 1130, x + w, 1198), radius=22, fill="#FFFFFF", outline=LINE, width=2)
        center_text(d, (x, 1130, x + w, 1198), chip, font(28, "medium"), BLUE)
        x += w + 24
    save(img, locale, "04-pyonta-plus")


def review_screenshot(locale: str) -> None:
    img = Image.new("RGBA", (W, H), "#EEF2F4")
    d = ImageDraw.Draw(img)
    draw_mac_window(img, (560, 300, 2320, 1500), "Pyonta")
    d.rectangle((602, 422, 2278, 1410), fill="#F6F8FA")
    draw_plus_alert(img, locale, (810, 650, 2070, 1100))
    out_dir = OUT / "review"
    out_dir.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_dir / f"pyonta-plus-required-{locale}-2880x1800.png", optimize=True)


def save(img: Image.Image, locale: str, name: str) -> None:
    out_dir = OUT / locale
    out_dir.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_dir / f"{name}.png", optimize=True)


def main() -> None:
    for locale in LOCALES:
        screenshot_receive(locale)
        screenshot_send(locale)
        screenshot_qr(locale)
        screenshot_plus(locale)
        review_screenshot(locale)


if __name__ == "__main__":
    main()
