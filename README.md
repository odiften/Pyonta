# Pyonta

**Pyonta** is a macOS app for receiving and sending files between Mac and Android devices using Google's Quick Share (formerly Nearby Share) protocol.

The app lives in your menu bar. Files received from Android are saved to your Downloads folder. To send files from Mac to Android, right-click in Finder → Share → Pyonta.

[Protocol documentation](/PROTOCOL.md) is available separately.

## Background

Apple's AirDrop is Apple-only. Google's Quick Share works between Android, Windows, and ChromeOS. Macs are stuck in the middle. Pyonta fills that gap.

While AirDrop compatibility is being rolled out to Pixel 10 and newer Samsung devices in 2026, the vast majority of Android phones still need a third-party solution to talk to a Mac.

## Status

Pyonta is in early development. The basic send/receive flow works for most file types, including images, videos, PDFs, and arbitrary files. Text and URLs are supported as well.

Distribution to the Mac App Store is planned. For now, you can build from source.

## Limitations (inherited from the Quick Share protocol)

* **Wi-Fi LAN only.** Both devices must be on the same Wi-Fi network. Bluetooth and Wi-Fi Direct are not supported.
* **Visible to everyone on your network at all times** while the app is running. Quick Share's "contacts only" mode requires Google account integration that is not feasible for a third-party Mac client.
* **Mac is invisible to Android by default.** Android only advertises its receive endpoint after detecting a Bluetooth Low Energy beacon, which Macs cannot send. To send from Mac to Android, either open Quick Share's receiving screen on the Android side first, or use Pyonta's QR code mode.

## Build from source

Requirements: Xcode 15 or later, an Apple ID. App Store distribution requires Apple Developer Program membership.

```
git clone https://github.com/odiften/Pyonta.git
cd Pyonta
open Pyonta.xcodeproj
```

In Xcode, set the Team to your own under Signing & Capabilities for both the **Pyonta** and **ShareExtension** targets, then ▶︎ Run.

## Credits

Pyonta is a fork of [grishka/NearDrop](https://github.com/grishka/NearDrop). NearDrop did the hard reverse-engineering work of the Quick Share protocol and built the original Swift implementation. Pyonta is licensed under the same Unlicense terms.

## License

[Unlicense](/UNLICENSE) — public domain dedication. Do whatever you want.

## About

Pyonta is built by [odiften](https://odiften.com), Imamura Takuya's solo development practice. Inquiries: https://odiften.com
