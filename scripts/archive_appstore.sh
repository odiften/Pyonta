#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

usage() {
	cat <<'EOF'
Usage:
  REVENUECAT_API_KEY=appl_... ./scripts/archive_appstore.sh

Optional:
  ARCHIVE_PATH=build/archives/Pyonta.xcarchive
  ALLOW_PROVISIONING_UPDATES=1

This script injects the RevenueCat public SDK key at build time. Do not commit
the key to the repository.
EOF
}

case "${1:-}" in
	-h|--help)
		usage
		exit 0
		;;
esac

api_key="${REVENUECAT_API_KEY:-}"
if [[ -z "$api_key" || "$api_key" == "REVENUECAT_PUBLIC_API_KEY" ]]; then
	cat >&2 <<'EOF'
Missing REVENUECAT_API_KEY.

Create the Pyonta app in RevenueCat, connect the Apple App Store app,
copy the Apple platform public SDK key, then run:
  REVENUECAT_API_KEY=appl_... ./scripts/archive_appstore.sh
EOF
	exit 64
fi

if [[ "$api_key" == test_* ]]; then
	cat >&2 <<'EOF'
REVENUECAT_API_KEY is a RevenueCat Test Store key.

Do not submit App Store builds with a test_ key. Connect the Apple App Store
app in RevenueCat, copy the Apple platform public SDK key, and rerun:
  REVENUECAT_API_KEY=appl_... ./scripts/archive_appstore.sh
EOF
	exit 64
fi

if [[ "$api_key" != appl_* ]]; then
	cat >&2 <<'EOF'
Warning: REVENUECAT_API_KEY does not start with "appl_".
Continue only if RevenueCat shows this as the Apple public SDK key for Pyonta.
EOF
fi

timestamp="$(date +%Y%m%d-%H%M%S)"
archive_path="${ARCHIVE_PATH:-$repo_root/build/archives/Pyonta-$timestamp.xcarchive}"
mkdir -p "$(dirname "$archive_path")"

args=(
	xcodebuild
	-project Pyonta.xcodeproj
	-scheme Pyonta
	-configuration Release
	-destination "generic/platform=macOS"
	-archivePath "$archive_path"
	REVENUECAT_API_KEY="$api_key"
)

if [[ "${ALLOW_PROVISIONING_UPDATES:-0}" == "1" ]]; then
	args+=(-allowProvisioningUpdates)
fi

args+=(archive)

"${args[@]}"

echo "Archive created: $archive_path"
