#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="${1:-$ROOT/Expando.app}"
SPARKLE_VERSION="${SPARKLE_VERSION:-2.6.4}"
SPARKLE_DIR="$ROOT/.sparkle-tools"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Sparkle embed skipped (not macOS)"
  exit 0
fi

if [[ ! -d "$APP/Contents" ]]; then
  echo "App bundle not found: $APP" >&2
  exit 1
fi

if [[ ! -d "$SPARKLE_DIR/Sparkle.framework" ]]; then
  mkdir -p "$SPARKLE_DIR"
  curl -fsSL "https://github.com/sparkle-project/Sparkle/releases/download/${SPARKLE_VERSION}/Sparkle-${SPARKLE_VERSION}.tar.xz" \
    -o "$SPARKLE_DIR/sparkle.tar.xz"
  tar -xJf "$SPARKLE_DIR/sparkle.tar.xz" -C "$SPARKLE_DIR"
fi

FRAMEWORKS="$APP/Contents/Frameworks"
MACOS="$APP/Contents/MacOS"
mkdir -p "$FRAMEWORKS"
rm -rf "$FRAMEWORKS/Sparkle.framework"
cp -R "$SPARKLE_DIR/Sparkle.framework" "$FRAMEWORKS/"

if [[ -d "$SPARKLE_DIR/Sparkle.app/Contents/Frameworks/Sparkle.framework" ]]; then
  :
fi

HELPER_SRC="$ROOT/scripts/sparkle-helper.m"
HELPER_BIN="$MACOS/expando-sparkle"
if [[ -f "$HELPER_SRC" ]]; then
  clang -fobjc-arc -framework Cocoa -framework Sparkle \
    -F "$FRAMEWORKS" \
    -Wl,-rpath,@executable_path/../Frameworks \
    "$HELPER_SRC" -o "$HELPER_BIN"
  chmod +x "$HELPER_BIN"
  echo "Built Sparkle helper at $HELPER_BIN"
fi

if command -v plutil >/dev/null 2>&1; then
  plutil -replace SUEnableAutomaticChecks -bool YES "$APP/Contents/Info.plist" 2>/dev/null || true
fi

echo "Embedded Sparkle.framework in $APP"
