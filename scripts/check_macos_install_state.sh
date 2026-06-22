#!/usr/bin/env bash
set -euo pipefail

mode="no-numbered"

usage() {
	cat <<'EOF'
Usage:
  ./scripts/check_macos_install_state.sh
  ./scripts/check_macos_install_state.sh --require-clean

Checks the local macOS install state for Pyonta.

Default mode fails if /Applications contains a numbered or otherwise
unexpected Pyonta app such as "Pyonta 2.app".

--require-clean fails if any Pyonta app is installed in /Applications, any
Pyonta process is running, or any Login Item named Pyonta exists. Use this
before installing from TestFlight or the App Store so macOS will not create
"Pyonta 2.app".
EOF
}

case "${1:-}" in
	"")
		;;
	--require-clean)
		mode="require-clean"
		;;
	-h|--help)
		usage
		exit 0
		;;
	*)
		usage >&2
		exit 64
		;;
esac

shopt -s nullglob

status=0
apps=(/Applications/Pyonta*.app)
unexpected_apps=()

echo "Pyonta macOS install state"
echo "mode=$mode"

if ((${#apps[@]} == 0)); then
	echo "applications=none"
else
	echo "applications=${#apps[@]}"
	for app in "${apps[@]}"; do
		name="$(basename "$app")"
		bundle_id="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$app/Contents/Info.plist" 2>/dev/null || true)"
		version="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$app/Contents/Info.plist" 2>/dev/null || true)"
		build="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' "$app/Contents/Info.plist" 2>/dev/null || true)"
		receipt="none"
		if [[ -f "$app/Contents/_MASReceipt/receipt" ]]; then
			receipt="mas"
		fi
		echo "app=$app bundleId=${bundle_id:-unknown} version=${version:-unknown} build=${build:-unknown} receipt=$receipt"
		if [[ "$name" != "Pyonta.app" ]]; then
			unexpected_apps+=("$app")
		fi
	done
fi

processes=()
while IFS= read -r pid; do
	[[ -n "$pid" ]] || continue
	command="$(ps -p "$pid" -o pid=,command= 2>/dev/null || true)"
	processes+=("${command:-$pid Pyonta}")
done < <(pgrep -x Pyonta 2>/dev/null || true)

if ((${#processes[@]} == 0)); then
	echo "processes=none"
else
	echo "processes=${#processes[@]}"
	for process in "${processes[@]}"; do
		echo "process=$process"
	done
fi

login_items="$(osascript -e 'tell application "System Events" to get the name of every login item' 2>/dev/null || true)"
if [[ "$login_items" == *Pyonta* ]]; then
	echo "loginItems=$login_items"
else
	echo "loginItems=no Pyonta"
fi

if ((${#unexpected_apps[@]} > 0)); then
	status=2
	echo "error=unexpected Pyonta app name in /Applications"
	for app in "${unexpected_apps[@]}"; do
		echo "unexpectedApp=$app"
	done
fi

if [[ "$mode" == "require-clean" ]]; then
	if ((${#apps[@]} > 0)); then
		status=2
		echo "error=Pyonta app exists in /Applications"
	fi
	if ((${#processes[@]} > 0)); then
		status=2
		echo "error=Pyonta process is running"
	fi
	if [[ "$login_items" == *Pyonta* ]]; then
		status=2
		echo "error=Pyonta Login Item exists"
	fi
fi

exit "$status"
