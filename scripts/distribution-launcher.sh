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

_python_is_312() {
  "$1" -c 'import sys; exit(0 if sys.version_info[:2] == (3, 12) else 1)' 2>/dev/null
}

FRAMEWORK_VERSIONS="$APP_DIR/Contents/Frameworks/Python.framework/Versions"
if [[ -d "$FRAMEWORK_VERSIONS" ]]; then
  for py in "$FRAMEWORK_VERSIONS"/3.12/bin/python3.12 "$FRAMEWORK_VERSIONS"/*/bin/python3.12; do
    if [[ -x "$py" ]]; then
      exec "$py" -m expando "$@"
    fi
  done
fi

for candidate in \
  /opt/homebrew/opt/python@3.12/bin/python3.12 \
  /opt/homebrew/bin/python3.12 \
  /usr/local/opt/python@3.12/bin/python3.12 \
  /usr/local/bin/python3.12 \
  /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 \
  "$(command -v python3.12 2>/dev/null || true)"
do
  if [[ -n "$candidate" && -x "$candidate" ]] && _python_is_312 "$candidate"; then
    exec "$candidate" -m expando "$@"
  fi
done

osascript -e 'display alert "Expando" message "Python 3.12 runtime missing. Install with Homebrew cask or install python@3.12, then reopen Expando."'
exit 1
