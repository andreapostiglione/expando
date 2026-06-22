#!/usr/bin/env bash
set -euo pipefail

APP="${1:?app bundle path required}"
ROOT="${2:?project root required}"

RESOURCES="$APP/Contents/Resources"
SITE_PACKAGES="$RESOURCES/site-packages"

rm -rf "$SITE_PACKAGES" "$RESOURCES/venv" "$APP/Contents/Frameworks/Python.framework"
mkdir -p "$SITE_PACKAGES"

python3 -m pip install -q "$ROOT" --target "$SITE_PACKAGES" --no-cache-dir

PYTHONPATH="$SITE_PACKAGES" python3 -c "import expando; print(expando.__version__)"
echo "Bundled expando into $SITE_PACKAGES"