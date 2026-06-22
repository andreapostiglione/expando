#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
RESOURCES="$APP_DIR/Contents/Resources"
SITE_PACKAGES="$RESOURCES/site-packages"
export PYTHONPATH="$SITE_PACKAGES${PYTHONPATH:+:$PYTHONPATH}"
export EXPANDO_RESOURCES="$RESOURCES"

if [[ $# -eq 0 ]]; then
  set -- run
fi

FRAMEWORK_VERSIONS="$APP_DIR/Contents/Frameworks/Python.framework/Versions"
if [[ -d "$FRAMEWORK_VERSIONS" ]]; then
  for py in "$FRAMEWORK_VERSIONS"/*/bin/python3; do
    if [[ -x "$py" ]]; then
      exec "$py" -m expando "$@"
    fi
  done
fi

for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
  if [[ -x "$candidate" ]] && "$candidate" -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    exec "$candidate" -m expando "$@"
  fi
done

osascript -e 'display alert "Expando" message "Python runtime missing from the app bundle. Reinstall from the latest GitHub release."'
exit 1