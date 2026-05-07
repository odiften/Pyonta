# Pyonta AppIcon: AI Image Generation Prompts

ユーザー側で AI 画像生成サービスを使って 1024×1024 のメインアイコンを生成するための仕様書。

## 共通仕様

- **出力サイズ**: 1024×1024 PNG（透過 NG、フルブリード）
- **形状**: macOS Big Sur 以降の Squircle（角丸スクエア）。Xcode 側で Squircle 化はしないので画像内で完結
- **マスコット**: 跳んでいる白うさぎ、前足にファイル/書類を抱えている
- **配色**: ピーチコーラル `#FF8A80`〜`#FFB199` の暖色グラデ背景
- **テキスト一切なし**（ロゴタイプはアイコンに入れない）
- **避ける**: Apple ロゴ、Quick Share ロゴ、Mac のシルエット、テキスト、リアル写真調

## DALL-E 3 / ChatGPT 用プロンプト（推奨）

```
A macOS app icon, 1024x1024 pixels, in the modern Big Sur squircle (rounded square) shape that fully fills the canvas with no padding. The icon shows a cute, simplified white rabbit mascot frozen mid-jump, ears flowing slightly back from upward motion, holding a small white document/paper in its front paws. The rabbit is rendered in a clean, friendly, slightly chunky vector illustration style — flat shading with subtle soft highlights, no outlines, no text. Background is a smooth diagonal gradient from peach (#FF8A80) at the top-left to soft coral (#FFB199) at the bottom-right. A faint dotted arc behind the rabbit hints at its jumping trajectory. The composition is centered, balanced, with the rabbit occupying about 55-65% of the canvas height. Style references: Apple's first-party app icons (Reminders, Notes, Calendar) — simple, polished, immediately legible at small sizes. No Apple logo, no Quick Share logo, no Mac silhouette, no words anywhere.
```

**指示時の補足**:
- 「Generate at 1024x1024」と明示
- 必要なら「Make 4 variations」で複数案生成 → 取捨選択
- 仕上がりが暗い場合「brighter, more vibrant peach background」を追加
- うさぎの表情が凶暴なら「friendly, gentle expression, soft eyes」を追加

## Midjourney 用プロンプト

```
macOS app icon, rounded square shape filling the whole canvas, cute chubby white rabbit mascot mid-jump holding a small paper document in its front paws, ears trailing slightly from upward motion, peach to coral gradient background (#FF8A80 to #FFB199), faint dotted jump arc behind, flat vector illustration style, soft subtle highlights, no outlines, no text, immediately legible, in the style of Apple first-party app icons like Reminders or Calendar, polished, friendly, centered composition --ar 1:1 --style raw --v 6.1 --no text logos words letters apple
```

## Stable Diffusion (SDXL) 用プロンプト

```
Positive: macOS app icon design, rounded square canvas, cute white rabbit mascot character mid-jump, holding small paper document in paws, peach coral gradient background, flat vector illustration, soft shading, friendly expression, polished, centered, 1024x1024, sharp clean lines, professional app icon style

Negative: text, words, letters, logos, apple logo, quick share logo, mac computer, realistic photo, 3D render, ugly, scary, dark, gritty, complex background, multiple rabbits, distorted anatomy, watermark
```

## 取捨選択の判断基準

複数生成されたら以下で評価:

| チェック | 合格条件 |
|---|---|
| 16px に縮小しても何が描いてあるかわかる | うさぎの耳のシルエットが識別可能 |
| 表情が「友好的」 | 怖い目・歯が見えない |
| 配色 | 背景は暖色（緑・青・紫が混ざっていない） |
| ファイル要素 | 書類/紙の白い四角が前足に確認できる |
| 跳躍感 | 影や motion line で「上向きの動き」がわかる |
| ノイズ | テキスト・ロゴ・余計な小物が無い |

## 商標観点での独自性チェック

「跳ぶ白うさぎ + ファイル」の組み合わせで先行登録がないことが理想。生成後に以下で確認:
- USPTO TESS で 9 類「Computer software」のうさぎロゴを画像検索（JPO や WIPO branddb も同様）
- Google 画像検索で類似アイコンを目視確認
- 既存アプリで似たアイコンがある場合、表情・ポーズ・配色のいずれかで差をつける

## 生成後の処理

1. 1024×1024 PNG として保存
2. `~/Projects/pyonta/Pyonta/design/appicon-master.png` に配置
3. `design/generate-appicon.sh` を実行（後述）
4. ビルド確認
