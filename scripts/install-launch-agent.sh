#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_SRC="$ROOT/scripts/com.andreapostiglione.expando.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.andreapostiglione.expando.plist"
OLD_PLIST="$HOME/Library/LaunchAgents/com.inochisrl.expando.plist"
LAUNCH_SCRIPT="$ROOT/scripts/launch-expando.sh"

chmod +x "$LAUNCH_SCRIPT"

mkdir -p "$HOME/Library/Application Support/expando"
mkdir -p "$HOME/Library/LaunchAgents"

# Rimuovi vecchio launch agent se presente
launchctl bootout "gui/$(id -u)/com.inochisrl.expando" 2>/dev/null || true
rm -f "$OLD_PLIST"

sed \
  -e "s|__EXPANDO_ROOT__|$ROOT|g" \
  -e "s|__HOME__|$HOME|g" \
  "$PLIST_SRC" > "$PLIST_DST"

launchctl bootout "gui/$(id -u)/com.andreapostiglione.expando" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
launchctl enable "gui/$(id -u)/com.andreapostiglione.expando"
launchctl kickstart -k "gui/$(id -u)/com.andreapostiglione.expando"

echo "Launch agent installato: $PLIST_DST"
echo "Expando partirà automaticamente ad ogni login."