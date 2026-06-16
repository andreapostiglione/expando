#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_SRC="$ROOT/scripts/com.inochisrl.expando.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.inochisrl.expando.plist"
LAUNCH_SCRIPT="$ROOT/scripts/launch-expando.sh"

chmod +x "$LAUNCH_SCRIPT"

mkdir -p "$HOME/Library/Application Support/expando"
mkdir -p "$HOME/Library/LaunchAgents"

sed \
  -e "s|__EXPANDO_ROOT__|$ROOT|g" \
  -e "s|__HOME__|$HOME|g" \
  "$PLIST_SRC" > "$PLIST_DST"

launchctl bootout "gui/$(id -u)/com.inochisrl.expando" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
launchctl enable "gui/$(id -u)/com.inochisrl.expando"
launchctl kickstart -k "gui/$(id -u)/com.inochisrl.expando"

echo "Launch agent installato: $PLIST_DST"
echo "Expando partirà automaticamente ad ogni login."