#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/Expando.app"
DMG="$ROOT/Expando.dmg"
STAGE="$ROOT/.dmg-stage"
DISTRIBUTION="${EXPANDO_DISTRIBUTION:-1}"
SIGN="${EXPANDO_SIGN:-1}"
NOTARIZE="${EXPANDO_NOTARIZE:-0}"

EXPANDO_DISTRIBUTION="$DISTRIBUTION" "$ROOT/scripts/build-macos-app.sh"

if [[ "$SIGN" == "1" ]]; then
  "$ROOT/scripts/codesign-app.sh"
fi

rm -rf "$STAGE" "$DMG"
mkdir -p "$STAGE"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"

hdiutil create -volname "Expando" -srcfolder "$STAGE" -ov -format UDZO "$DMG"
rm -rf "$STAGE"

if [[ "$NOTARIZE" == "1" ]]; then
  "$ROOT/scripts/notarize-dmg.sh" "$DMG"
fi

echo "Built $DMG (distribution=$DISTRIBUTION, signed=$SIGN, notarized=$NOTARIZE)"