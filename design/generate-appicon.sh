#!/bin/bash
# Pyonta AppIcon: マスター 1024×1024 PNG から AppIcon.appiconset の全サイズを生成
#
# 使い方:
#   1. AI で生成した 1024×1024 PNG を design/appicon-master.png に置く
#   2. このスクリプトを実行: ./design/generate-appicon.sh
#   3. Xcode で再ビルド
#
# 前提: macOS 標準の sips コマンドを使用、追加インストール不要

set -euo pipefail

cd "$(dirname "$0")/.."  # → Pyonta リポジトリのルート

MASTER="design/appicon-master.png"
APPICON_DIR="Pyonta/Assets.xcassets/AppIcon.appiconset"
SHARE_ICON_DIR="ShareExtension/Assets.xcassets/PyontaIcon.imageset"

if [[ ! -f "$MASTER" ]]; then
  echo "Error: $MASTER not found." >&2
  echo "Place the AI-generated 1024x1024 PNG at $MASTER first." >&2
  exit 1
fi

# マスターの寸法確認
W=$(sips -g pixelWidth "$MASTER" | awk '/pixelWidth/ {print $2}')
H=$(sips -g pixelHeight "$MASTER" | awk '/pixelHeight/ {print $2}')
if [[ "$W" != "1024" || "$H" != "1024" ]]; then
  echo "Warning: master is ${W}x${H}, expected 1024x1024. Will resize anyway." >&2
fi

echo "Generating AppIcon sizes..."

# AppIcon.appiconset の Contents.json で参照されている全ファイルを生成
# size×scale の組み合わせ: 16@1x/2x, 32@1x/2x, 128@1x/2x, 256@1x/2x, 512@1x/2x
# 「N 1.png」「N.png」のペアは Xcode のデフォルト命名（同じ画素サイズで idiom 違いに使う想定）

generate() {
  local px="$1"
  local out="$2"
  sips -s format png -z "$px" "$px" "$MASTER" --out "$APPICON_DIR/$out" >/dev/null
  echo "  $out (${px}x${px})"
}

generate 16   "16.png"
generate 32   "32.png"        # 16@2x
generate 32   "32 1.png"      # 32@1x
generate 64   "64.png"        # 32@2x
generate 128  "128.png"
generate 256  "256.png"       # 128@2x
generate 256  "256 1.png"     # 256@1x
generate 512  "512.png"       # 256@2x
generate 512  "512 1.png"     # 512@1x
generate 1024 "1024.png"      # 512@2x

echo ""
echo "Generating ShareExtension PyontaIcon sizes..."

generate_share() {
  local px="$1"
  local out="$2"
  sips -s format png -z "$px" "$px" "$MASTER" --out "$SHARE_ICON_DIR/$out" >/dev/null
  echo "  $out (${px}x${px})"
}

generate_share 16 "16.png"
generate_share 32 "32.png"

echo ""
echo "Done. Rebuild in Xcode to apply."
echo ""
echo "Next steps:"
echo "  - xcodebuild -project Pyonta.xcodeproj -scheme Pyonta -configuration Release build"
echo "  - cp -R build/.../Pyonta.app /Applications/"
echo "  - Verify icon in Finder and Dock"
