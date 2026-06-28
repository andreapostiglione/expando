#!/usr/bin/env bash
set -euo pipefail

APP="${1:?app bundle path required}"

if [[ -d "$APP/Contents/Resources/venv" ]]; then
  echo "Legacy non-relocatable venv must not ship in distribution builds" >&2
  exit 1
fi

if [[ ! -d "$APP/Contents/Resources/site-packages/expando" ]]; then
  echo "Missing bundled site-packages/expando" >&2
  exit 1
fi

if [[ ! -f "$APP/Contents/Resources/default_config/config/default.yml" ]]; then
  echo "Missing bundled default_config/config/default.yml" >&2
  exit 1
fi

if [[ ! -f "$APP/Contents/Resources/packages/hub/index.json" ]]; then
  echo "Missing bundled packages/hub/index.json" >&2
  exit 1
fi

if [[ ! -x "$APP/Contents/Resources/scripts/install-launch-agent.sh" ]]; then
  echo "Missing bundled install-launch-agent.sh" >&2
  exit 1
fi

if ! grep -q '../MacOS/expando' "$APP/Contents/Resources/scripts/launch-expando.sh"; then
  echo "Bundled launch agent script must resolve Contents/MacOS/expando" >&2
  exit 1
fi

if grep -q '/Users/runner/' "$APP/Contents/MacOS/expando" 2>/dev/null; then
  echo "Launcher contains CI runner paths" >&2
  exit 1
fi

SPARKLE_HELPER="$APP/Contents/MacOS/expando-sparkle"
if [[ -x "$SPARKLE_HELPER" ]] && otool -L "$SPARKLE_HELPER" | grep -q '@rpath/Sparkle.framework'; then
  if ! otool -l "$SPARKLE_HELPER" | grep -q '@executable_path/../Frameworks'; then
    echo "Sparkle helper is missing @executable_path/../Frameworks rpath" >&2
    exit 1
  fi
fi

export PYTHONPATH="$APP/Contents/Resources/site-packages${PYTHONPATH:+:$PYTHONPATH}"
python3 -c "from expando.paths import package_root; root = package_root(); assert (root / 'default_config' / 'config' / 'default.yml').is_file(), root; import expando"

PY312="${EXPANDO_VERIFY_PYTHON312:-$(command -v python3.12 || true)}"
if [[ -z "$PY312" ]]; then
  echo "python3.12 is required to verify bundled native dependencies" >&2
  exit 1
fi
PYTHONPATH="$APP/Contents/Resources/site-packages${PYTHONPATH:+:$PYTHONPATH}" "$PY312" - <<'PY'
import AppKit
import objc
from pynput import keyboard

assert AppKit is not None
assert objc is not None
assert keyboard is not None
PY

"$APP/Contents/MacOS/expando" --version >/dev/null
echo "Distribution bundle verification passed for $APP"
