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

if [[ "$SIGN" == "1" ]]; then
  IDENTITY="${EXPANDO_SIGN_IDENTITY:-}"
  if [[ -z "$IDENTITY" ]]; then
    IDENTITY="$(security find-identity -v -p codesigning | sed -n 's/.*"\(Developer ID Application:.*\)"/\1/p' | head -1)"
  fi
  if [[ -z "$IDENTITY" ]]; then
    echo "No Developer ID signing identity found for DMG. Set EXPANDO_SIGN_IDENTITY." >&2
    exit 1
  fi
  codesign --force --timestamp --sign "$IDENTITY" "$DMG"
  codesign --verify --verbose=2 "$DMG"
fi

if [[ "$NOTARIZE" == "1" ]]; then
  "$ROOT/scripts/notarize-dmg.sh" "$DMG"
fi

echo "Built $DMG (distribution=$DISTRIBUTION, signed=$SIGN, notarized=$NOTARIZE)"
