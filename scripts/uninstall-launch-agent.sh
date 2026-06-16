#!/usr/bin/env bash
set -euo pipefail

PLIST_DST="$HOME/Library/LaunchAgents/com.andreapostiglione.expando.plist"
OLD_PLIST="$HOME/Library/LaunchAgents/com.inochisrl.expando.plist"

launchctl bootout "gui/$(id -u)/com.andreapostiglione.expando" 2>/dev/null || true
launchctl bootout "gui/$(id -u)/com.inochisrl.expando" 2>/dev/null || true
rm -f "$PLIST_DST" "$OLD_PLIST"

echo "Launch agent rimosso."