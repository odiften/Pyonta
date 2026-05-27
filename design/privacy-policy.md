# Pyonta Privacy Policy（草案）

odiften.com に `/pyonta/privacy` として配置する想定。日本語と英語を併記（世界向け配布のため英語が一次、日本語は補助）。最終的には HTML 化して odiften.com の既存 privacy.html のスタイル（Inter + Noto Sans JP、グレー基調）に合わせる。

最終更新日: 2026-05-27 / Last updated: May 27, 2026

---

## English

### 1. Overview

Pyonta is a macOS application that lets you receive files, text, and URLs from Android devices via the Google Quick Share protocol, and send files from your Mac to Android devices in return. This policy describes what data Pyonta handles and how it is treated.

**TL;DR**: Pyonta is designed to keep your transfer data on your devices. We do not run any transfer servers, do not collect analytics, and do not transmit your file contents to odiften or third parties. Purchases and entitlement checks for Pyonta+ are handled through Apple StoreKit and RevenueCat.

### 2. Information We Do Not Collect

Pyonta does **not** collect, transmit, or store any of the following on remote servers:

- The contents, names, or metadata of files you send or receive
- Text or URLs shared through the app
- Local network peer information such as Quick Share device names, local IP addresses, or hardware identifiers
- Usage statistics, crash logs, or diagnostic data
- Any personally identifiable information (name, email, location, etc.)

We do not operate any servers that receive your transfer data. Pyonta has no analytics SDK embedded.

### 3. Information Handled Locally on Your Mac

The following data is handled entirely on your Mac and never leaves it via Pyonta:

| Data | Where It Lives | Why It Exists |
|---|---|---|
| Files received from Android | Your `Downloads` folder (or a folder you choose) | The core function of Pyonta |
| Text received from Android | Your system clipboard | Convenience: you paste it where you want |
| URLs received from Android | Opened in your default browser | Convenience |
| App preferences (auto-accept, visibility, etc.) | macOS `UserDefaults` for the Pyonta app | Settings persistence |
| Notifications | macOS Notification Center | Standard macOS user notifications |

### 4. Local Network Communication

To find nearby Android devices and exchange files, Pyonta uses the Google Quick Share protocol over your local Wi-Fi network. This involves:

- **Bonjour/mDNS broadcasts**: Pyonta advertises a service on your local network so Android devices can discover your Mac. The broadcast contains a randomly generated session identifier; it does not contain your name, email, or any personal data.
- **Direct TCP connection**: Once an Android device initiates a transfer, Pyonta and the Android device communicate directly over your local network. All data is encrypted using AES-256-CBC with HMAC-SHA256, with keys exchanged via the UKEY2 protocol (P-256 ECDH).
- **No internet connection is used** for the file transfer itself.

You can disable Bonjour broadcasting at any time using the "Visible to everyone" toggle in the menu bar. When disabled, your Mac will not appear in the Quick Share device picker on Android devices.

### 5. Permissions Pyonta Requests

| Permission | Why |
|---|---|
| Local Network access | Required to discover Android devices on your Wi-Fi |
| Notifications | To alert you when an Android device wants to send you something |
| Downloads folder access | To save received files to your Downloads folder |
| User-selected file access | To read files you choose to send to Android |

Pyonta does **not** request access to your camera, microphone, contacts, calendar, photos, location, or any other sensitive data.

### 6. In-App Purchases

Pyonta uses Apple StoreKit and RevenueCat to process Pyonta+ purchases, restore purchases, and check whether Pyonta+ is active.

For this purpose, purchase-related information may be processed by Apple and RevenueCat, such as:

- An anonymous RevenueCat app user identifier
- App Store product identifiers and transaction/receipt information
- Purchase, subscription, restore, and entitlement status
- App version, platform, and similar technical information needed to operate purchases

Pyonta does **not** send file contents, file names, shared text, shared URLs, Quick Share device names, or local network transfer data to RevenueCat. Payment details such as credit card numbers are handled by Apple; odiften and Pyonta do not receive them.

RevenueCat's privacy policy is available at <https://www.revenuecat.com/privacy>.

### 6.1 This Website

This privacy policy page is hosted on odiften.com. odiften.com uses Google Analytics to understand website traffic. This website analytics setup is separate from the Pyonta app itself. The Pyonta app does not include Google Analytics.

### 7. Data Retention

- Files you receive remain in your `Downloads` folder until you delete them.
- App preferences remain on your Mac until you uninstall Pyonta.
- We do not retain transfer data on our servers because we do not operate a transfer server.
- Purchase and entitlement records are retained by Apple and RevenueCat according to their own policies and are used to provide Pyonta+ access and purchase support.

### 8. Children's Privacy

Pyonta is not directed at children under the age of 13 and does not knowingly collect any data from children. Because Pyonta does not collect personal data from anyone, this policy applies equally regardless of age.

### 9. Changes to This Policy

We may update this policy from time to time. Material changes will be reflected on this page with an updated "Last updated" date. Continued use of Pyonta after a policy update constitutes acceptance of the revised policy.

### 10. Contact

For questions about this policy, please contact us at <info@odiften.com>.

This app is developed and operated by **odiften**.

---

## 日本語

### 1. 概要

Pyonta は、Google Quick Share プロトコルを利用して Android 端末から Mac へファイル・テキスト・URL を受信し、また Mac から Android へファイルを送信できる macOS アプリケーションです。本ポリシーは、Pyonta が扱うデータとその取り扱いを説明します。

**要約**: Pyonta は転送データを利用者の端末内に留めることを前提に設計されています。転送用サーバーを運用しておらず、分析データも収集せず、ファイルの内容を odiften や第三者に送信することもありません。Pyonta+ の購入処理と権利確認には Apple StoreKit と RevenueCat を使用します。

### 2. 収集しない情報

Pyonta は以下の情報を、リモートサーバーに**収集・送信・保管しません**:

- 送受信されたファイルの内容・ファイル名・メタデータ
- アプリを介して共有されたテキストや URL
- Quick Share の端末名、ローカル IP アドレス、ハードウェア識別子などのローカルネットワーク上の相手端末情報
- 利用統計・クラッシュログ・診断データ
- 氏名・メールアドレス・位置情報等の個人を特定できる情報

利用者の転送データを受け取るサーバーは一切運用していません。Pyonta には分析用 SDK も組み込まれていません。

### 3. Mac 内でのみ扱う情報

以下のデータは利用者の Mac 内でのみ扱われ、Pyonta を介して外部に送信されることはありません:

| データ | 保管先 | 目的 |
|---|---|---|
| Android から受信したファイル | `Downloads` フォルダ（または利用者が選択したフォルダ） | Pyonta の主機能 |
| Android から受信したテキスト | システムクリップボード | 利用者が任意の場所に貼り付けるため |
| Android から受信した URL | 既定のブラウザで開く | 利便性のため |
| アプリの設定（自動受諾・可視性 等） | macOS の `UserDefaults` | 設定の保持 |
| 通知 | macOS の通知センター | 標準の macOS 通知 |

### 4. ローカルネットワーク通信

近くの Android 端末を発見しファイルを交換するため、Pyonta は Wi-Fi 上で Google Quick Share プロトコルを使用します:

- **Bonjour / mDNS のブロードキャスト**: Android 端末から Mac を発見できるよう、ローカルネットワークにサービスを広告します。ブロードキャストにはランダム生成されたセッション識別子のみが含まれ、氏名・メール等の個人データは含まれません。
- **直接 TCP 接続**: Android 端末から転送が開始されると、Android と Pyonta はローカルネットワーク上で直接通信します。全データは UKEY2 プロトコル（P-256 ECDH）で交換した鍵を用いて AES-256-CBC + HMAC-SHA256 で暗号化されます。
- **ファイル転送自体にインターネット接続は使用しません。**

メニューバーの「Visible to everyone」トグルでブロードキャストをいつでも無効化できます。無効化中は、Android の Quick Share の送信先候補に Pyonta（あなたの Mac）が表示されません。

### 5. Pyonta が要求する権限

| 権限 | 理由 |
|---|---|
| ローカルネットワークへのアクセス | Wi-Fi 上の Android 端末を発見するため |
| 通知の表示 | Android からの送信要求を通知するため |
| Downloads フォルダへのアクセス | 受信ファイルを Downloads に保存するため |
| ユーザーが選択したファイルへのアクセス | Android へ送信するファイルを読み取るため |

Pyonta は、カメラ・マイク・連絡先・カレンダー・写真ライブラリ・位置情報、その他の機微情報へのアクセスは**一切要求しません**。

### 6. アプリ内課金

Pyonta は、Pyonta+ の購入処理、購入の復元、Pyonta+ が有効かどうかの確認のために、Apple StoreKit と RevenueCat を使用します。

この目的のため、Apple および RevenueCat では、以下のような購入関連情報が処理されることがあります:

- RevenueCat が発行する匿名のアプリ利用者 ID
- App Store の製品 ID、取引情報、レシート情報
- 購入、サブスクリプション、復元、権利状態
- 購入機能の提供に必要なアプリバージョン、プラットフォーム等の技術情報

Pyonta は、ファイルの内容、ファイル名、共有テキスト、共有 URL、Quick Share の端末名、ローカルネットワーク上の転送データを RevenueCat に送信しません。クレジットカード番号などの支払い情報は Apple が処理し、odiften および Pyonta は受け取りません。

RevenueCat のプライバシーポリシーは <https://www.revenuecat.com/privacy> で確認できます。

### 6.1 この Web サイトについて

本プライバシーポリシーページは odiften.com 上で公開されています。odiften.com では Web サイトのアクセス状況を把握するため Google Analytics を使用しています。これは Pyonta アプリ本体とは別の Web サイト用の計測です。Pyonta アプリには Google Analytics は含まれていません。

### 7. データの保管期間

- 受信したファイルは、利用者が削除するまで `Downloads` フォルダに残ります。
- アプリの設定は、Pyonta をアンインストールするまで Mac 内に残ります。
- 当事業者のサーバーに転送データを保管することはありません（そもそも転送用サーバーを運用していないため）。
- 購入および権利状態の記録は、Apple および RevenueCat の各ポリシーに従って保持され、Pyonta+ の提供と購入サポートに使用されます。

### 8. 子どものプライバシー

Pyonta は 13 歳未満の児童を対象としておらず、児童からのデータを意図的に収集することはありません。Pyonta は誰からも個人データを収集していないため、本ポリシーは年齢にかかわらず等しく適用されます。

### 9. ポリシーの変更

本ポリシーは必要に応じて改定されることがあります。重要な変更があった場合は本ページに反映し、「最終更新日」を更新します。改定後の Pyonta の継続利用は、改定ポリシーへの同意とみなします。

### 10. お問い合わせ

本ポリシーに関するお問い合わせは <info@odiften.com> までご連絡ください。

本アプリは **odiften** が開発・運営しています。
