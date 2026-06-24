#!/usr/bin/env bash
set -euo pipefail

# Standalone launcher for DMG distribution build.
# Uses embedded Python (no host Python dependency).

APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
RESOURCES="$APP_DIR/Contents/Resources"
SITE_PACKAGES="$RESOURCES/site-packages"
export EXPANDO_RESOURCES="$RESOURCES"

if [[ $# -eq 0 ]]; then
  set -- run
fi

# 1. Prefer fully embedded python-build-standalone runtime (ideal: no host dep)
PYTHON_EMBED="$RESOURCES/python"
if [[ -d "$PYTHON_EMBED" ]]; then
  PYBIN=$(find "$PYTHON_EMBED/bin" -name 'python3*' -type f -perm +111 2>/dev/null | head -1)
  if [[ -x "$PYBIN" ]]; then
    export PYTHONHOME="$PYTHON_EMBED"
    export PYTHONPATH="$SITE_PACKAGES${PYTHONPATH:+:$PYTHONPATH}"
    exec "$PYBIN" -m expando "$@"
  fi
fi

# 2. Legacy framework location (if someone manually placed Python.framework)
FRAMEWORK_VERSIONS="$APP_DIR/Contents/Frameworks/Python.framework/Versions"
if [[ -d "$FRAMEWORK_VERSIONS" ]]; then
  for py in "$FRAMEWORK_VERSIONS"/*/bin/python3; do
    if [[ -x "$py" ]]; then
      export PYTHONPATH="$SITE_PACKAGES${PYTHONPATH:+:$PYTHONPATH}"
      exec "$py" -m expando "$@"
    fi
  done
fi

# No system python fallback for true standalone DMG builds.
# If embedded python missing, user must reinstall DMG (no host Python visible/required).
osascript -e 'display alert "Expando" message "The app bundle is missing its embedded Python runtime. Please download the latest DMG from GitHub Releases."'
exit 1