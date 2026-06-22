#!/usr/bin/env python3
from __future__ import annotations

import generate_appstore_screenshots as g
from PIL import Image, ImageDraw


LOCALE = "ja"
OUT_DIR = g.OUT / "ja-large"

COPY = {
    "receiveTitle": "Android→Mac\nかんたん転送",
    "receiveBody": "共有から送るだけ。写真・動画・PDF・リンク・テキストをMacで受け取れます。",
    "sendTitle": "Mac → Android\nすぐ送信",
    "sendBody": "メニューバーやFinderの共有から、ファイルやクリップボードをAndroidへ送れます。",
    "qrTitle": "見つからない時も\nQRで接続",
    "qrBody": "端末が表示されない時も、QRコードで転送を続けられます。",
    "plusTitle": "Android受信を\nPyonta+で解放",
    "plusBody": "Macからの送信は無料。AndroidからMacへの受信はPyonta+で使えます。",
}


def save(img: Image.Image, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(OUT_DIR / f"{name}.png", optimize=True)


def base_large(title: str, body: str, accent: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (g.W, g.H), g.BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, g.W, g.H), fill=g.BG)
    d.ellipse((-320, -250, 760, 720), fill=g.rgba(g.BG2, 255))
    d.ellipse((2120, 1160, 3260, 2220), fill=g.rgba("#EDF4EA", 255))

    img.alpha_composite(g.app_icon(165), (150, 145))
    d.text((345, 172), "Pyonta", font=g.font(62, "bold"), fill=g.INK)
    d.text((348, 252), g.SUBTITLES[LOCALE], font=g.font(34, "medium"), fill=g.MUTED)

    d.rounded_rectangle((155, 365, 305, 421), radius=28, fill=accent)
    d.text((179, 377), "macOS", font=g.font(28, "bold"), fill="white")

    title_bottom = g.draw_text(d, (150, 510), title, g.font(118, "bold"), g.INK, 860, 22)
    body_y = max(870, title_bottom + 42)
    g.draw_text(d, (154, body_y), body, g.font(44, "regular"), g.MUTED, 740, 20)
    return img, d


def draw_large_menu_panel(img: Image.Image, rect) -> None:
    d = ImageDraw.Draw(img)
    g.shadow(img, rect, 36, 38)
    g.rounded(d, rect, 36, g.PANEL, "#DCE3EA", 2)
    x1, y1, x2, _ = rect
    y = y1 + 54
    items = [
        ("すべてのユーザーに公開", True),
        ("確認なしで受信", True),
        ("URLを自動で開く", False),
        ("ログイン時に起動", True),
    ]
    for label, on in items:
        d.text((x1 + 54, y + 6), label, font=g.font(36, "bold"), fill=g.INK)
        toggle_x = x2 - 142
        fill = g.GREEN if on else "#C9D1D9"
        d.rounded_rectangle((toggle_x, y, toggle_x + 86, y + 44), radius=22, fill=fill)
        knob_x = toggle_x + (46 if on else 4)
        d.ellipse((knob_x, y + 4, knob_x + 36, y + 40), fill="white")
        y += 82
    d.line((x1 + 34, y + 10, x2 - 34, y + 10), fill=g.LINE, width=3)
    y += 42
    for label in ("ファイルを送信…", "クリップボードを送信…", "Pyonta+: 未有効"):
        d.text((x1 + 54, y), label, font=g.font(34, "bold"), fill=g.INK)
        y += 70


def screenshot_receive() -> None:
    img, d = base_large(COPY["receiveTitle"], COPY["receiveBody"], g.BLUE)
    g.draw_mac_window(img, (1010, 235, 2685, 1455), "Pyonta")
    d.rectangle((1054, 358, 2642, 1365), fill="#F2F6F8")
    d.text((1160, 500), "MacBook Pro", font=g.font(72, "bold"), fill=g.INK)
    d.text((1164, 595), "Downloads", font=g.font(40, "medium"), fill=g.MUTED)
    draw_large_menu_panel(img, (1510, 318, 2565, 980))
    g.draw_phone(d, (930, 780, 1285, 1450))
    g.draw_arrow(d, (1300, 1040), (1490, 880), g.GREEN)
    d.rounded_rectangle((1210, 1238, 1980, 1330), radius=32, fill="#FFFFFF", outline=g.LINE, width=2)
    d.ellipse((1252, 1264, 1306, 1318), fill=g.GREEN)
    d.text((1338, 1260), "IMG_2042.jpg", font=g.font(38, "bold"), fill=g.INK)
    save(img, "01-receive-from-android")


def screenshot_send() -> None:
    img, d = base_large(COPY["sendTitle"], COPY["sendBody"], g.GREEN)
    g.draw_mac_window(img, (1025, 275, 2610, 1430), "ファイルを送信")
    d.text((1160, 445), "ファイルを送信…", font=g.font(70, "bold"), fill=g.INK)
    d.text((1164, 540), "クリップボードを送信…", font=g.font(42, "bold"), fill=g.MUTED)
    devices = [("Pixel 8 Pro", g.GREEN), ("Android device", g.BLUE)]
    for i, (name, color) in enumerate(devices):
        y = 700 + i * 150
        d.rounded_rectangle((1160, y, 2290, y + 116), radius=34, fill="#F7FAFB", outline=g.LINE, width=2)
        d.ellipse((1202, y + 32, 1260, y + 90), fill=color)
        d.text((1304, y + 30), name, font=g.font(46, "bold"), fill=g.INK)
        d.text((2130, y + 30), ">", font=g.font(48, "bold"), fill="#9DA8B3")
    d.rounded_rectangle((1160, 1100, 1765, 1194), radius=30, fill="#FFFFFF", outline=g.LINE, width=2)
    d.text((1228, 1124), "QRコードを使用...", font=g.font(36, "bold"), fill=g.BLUE)
    g.draw_phone(d, (2265, 800, 2615, 1470))
    g.draw_arrow(d, (2010, 1165), (2248, 1100), g.GREEN)
    save(img, "02-send-to-android")


def screenshot_qr() -> None:
    img, d = base_large(COPY["qrTitle"], COPY["qrBody"], g.AMBER)
    g.draw_mac_window(img, (1015, 255, 2635, 1450), "Pyonta")
    d.text((1240, 455), "QRコードをスキャン", font=g.font(70, "bold"), fill=g.INK)
    qr = g.qr_pattern(560)
    g.shadow(img, (1395, 590, 1955, 1150), 28, 20)
    img.alpha_composite(qr, (1395, 590))
    g.draw_text(d, (1244, 1225), "スキャンすると転送が自動で始まります。", g.font(42, "regular"), g.MUTED, 900, 12)
    g.draw_phone(d, (2220, 720, 2570, 1390))
    d.rounded_rectangle((2304, 908, 2484, 1088), radius=24, outline=g.BLUE, width=12)
    g.draw_arrow(d, (2160, 1000), (1965, 870), g.AMBER)
    save(img, "03-qr-fallback")


def screenshot_plus() -> None:
    img, d = base_large(COPY["plusTitle"], COPY["plusBody"], g.BLUE)
    g.draw_mac_window(img, (1025, 315, 2630, 1435), "Pyonta")
    d.rectangle((1068, 440, 2588, 1348), fill="#F3F6F8")
    g.draw_plus_alert(img, LOCALE, (1220, 655, 2490, 1115))
    chips = ["月額", "年額トライアル", "買い切り"]
    x = 1170
    for i, chip in enumerate(chips):
        w = [245, 350, 260][i]
        d.rounded_rectangle((x, 1230, x + w, 1310), radius=26, fill="#FFFFFF", outline=g.LINE, width=2)
        g.center_text(d, (x, 1230, x + w, 1310), chip, g.font(32, "bold"), g.BLUE)
        x += w + 30
    save(img, "04-pyonta-plus")


def main() -> None:
    screenshot_receive()
    screenshot_send()
    screenshot_qr()
    screenshot_plus()


if __name__ == "__main__":
    main()
