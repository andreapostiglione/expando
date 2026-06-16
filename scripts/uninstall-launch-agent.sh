#!/usr/bin/env bash
set -euo pipefail

PLIST_DST="$HOME/Library/LaunchAgents/com.inochisrl.expando.plist"

launchctl bootout "gui/$(id -u)/com.inochisrl.expando" 2>/dev/null || true
rm -f "$PLIST_DST"

echo "Launch agent rimosso."