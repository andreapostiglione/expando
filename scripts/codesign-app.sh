#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/Expando.app"
ENTITLEMENTS="$ROOT/scripts/entitlements.plist"

if [[ ! -d "$APP" ]]; then
  echo "Missing $APP — run build-macos-app.sh first" >&2
  exit 1
fi

IDENTITY="${EXPANDO_SIGN_IDENTITY:-}"
if [[ -z "$IDENTITY" ]]; then
  IDENTITY="$(security find-identity -v -p codesigning | sed -n 's/.*"\(Developer ID Application:.*\)"/\1/p' | head -1)"
fi

if [[ -z "$IDENTITY" ]]; then
  echo "No Developer ID signing identity found. Set EXPANDO_SIGN_IDENTITY." >&2
  exit 1
fi

echo "Signing with: $IDENTITY"

sign_macho() {
  local target="$1"
  if [[ -L "$target" ]]; then
    return 0
  fi
  if file "$target" | grep -q "Mach-O"; then
    codesign --force --options runtime --timestamp \
      --entitlements "$ENTITLEMENTS" \
      --sign "$IDENTITY" "$target"
  fi
}

while IFS= read -r -d '' candidate; do
  sign_macho "$candidate" || true
done < <(find "$APP" -type f \( -perm -111 -o -name "*.so" -o -name "*.dylib" \) -print0 2>/dev/null)

codesign --force --options runtime --timestamp \
  --entitlements "$ENTITLEMENTS" \
  --sign "$IDENTITY" "$APP/Contents/MacOS/expando"

HELPER="$APP/Contents/MacOS/expando-sparkle"
if [[ -f "$HELPER" ]] && file "$HELPER" | grep -q "Mach-O"; then
  codesign --force --options runtime --timestamp \
    --entitlements "$ENTITLEMENTS" \
    --sign "$IDENTITY" "$HELPER"
fi

codesign --force --options runtime --timestamp \
  --entitlements "$ENTITLEMENTS" \
  --sign "$IDENTITY" "$APP"

codesign --verify --deep --verbose=2 "$APP"
spctl --assess --type execute --verbose=4 "$APP" 2>/dev/null || true

echo "Signed $APP"
