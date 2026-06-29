#!/usr/bin/env bash
set -euo pipefail

# Repairs a broken DMG install when the bundled runtime assets are stale.
# Uses Python 3.12 for bundled site-packages and restores the native launcher.

APP="${1:-/Applications/Expando.app}"
ROOT="${2:-$(cd "$(dirname "$0")/.." && pwd)}"
RESOURCES="$APP/Contents/Resources"
SITE_PACKAGES="$RESOURCES/site-packages"

if [[ ! -d "$APP/Contents/MacOS" ]]; then
  echo "Expando.app not found at: $APP" >&2
  exit 1
fi

PYTHON=""
for candidate in \
  /opt/homebrew/opt/python@3.12/bin/python3.12 \
  /opt/homebrew/bin/python3.12 \
  /usr/local/opt/python@3.12/bin/python3.12 \
  /usr/local/bin/python3.12 \
  /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12
do
  if [[ -x "$candidate" ]] && "$candidate" -c 'import sys; exit(0 if sys.version_info[:2] == (3, 12) else 1)' 2>/dev/null; then
    PYTHON="$candidate"
    break
  fi
done

if [[ -z "$PYTHON" ]]; then
  echo "Python 3.12 not found. Install the current Expando DMG or Homebrew cask." >&2
  exit 1
fi

if [[ ! -f "$ROOT/scripts/expando-launcher.c" ]]; then
  echo "Native Expando launcher source not found at $ROOT/scripts/expando-launcher.c" >&2
  exit 1
fi

if ! command -v clang >/dev/null 2>&1; then
  echo "clang is required to repair the native launcher. Reinstall Expando instead." >&2
  exit 1
fi

rm -rf "$RESOURCES/venv"
mkdir -p "$SITE_PACKAGES"
"$PYTHON" -m pip install -q "$ROOT" --target "$SITE_PACKAGES" --upgrade --force-reinstall --no-cache-dir

clang -Wall -Wextra -O2 -mmacosx-version-min=12.0 \
  "$ROOT/scripts/expando-launcher.c" \
  -o "$APP/Contents/MacOS/expando"
chmod +x "$APP/Contents/MacOS/expando"
xattr -dr com.apple.quarantine "$APP" 2>/dev/null || true

echo "Repaired $APP using $PYTHON"
"$APP/Contents/MacOS/expando" --version
