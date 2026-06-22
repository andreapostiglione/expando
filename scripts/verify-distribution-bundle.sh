#!/usr/bin/env bash
set -euo pipefail

APP="${1:?app bundle path required}"

if command -v rg >/dev/null 2>&1; then
  if rg -n '/Users/runner/' "$APP" >/dev/null 2>&1; then
    echo "Bundle contains CI runner paths:" >&2
    rg -n '/Users/runner/' "$APP" >&2 || true
    exit 1
  fi
else
  if grep -R "/Users/runner/" "$APP" >/dev/null 2>&1; then
    echo "Bundle contains CI runner paths" >&2
    exit 1
  fi
fi

if [[ ! -d "$APP/Contents/Resources/site-packages/expando" ]]; then
  echo "Missing bundled site-packages/expando" >&2
  exit 1
fi

EMBEDDED_PY=""
for candidate in "$APP/Contents/Frameworks/Python.framework/Versions/"*/bin/python3; do
  if [[ -x "$candidate" ]]; then
    EMBEDDED_PY="$candidate"
    break
  fi
done

if [[ -z "$EMBEDDED_PY" ]]; then
  echo "Missing embedded Python.framework runtime" >&2
  exit 1
fi

export PYTHONPATH="$APP/Contents/Resources/site-packages${PYTHONPATH:+:$PYTHONPATH}"
"$EMBEDDED_PY" -c "import expando"

"$APP/Contents/MacOS/expando" --version >/dev/null
echo "Distribution bundle verification passed for $APP"