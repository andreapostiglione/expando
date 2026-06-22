#!/usr/bin/env bash
set -euo pipefail

APP="${1:?app bundle path required}"

if rg -n '/Users/runner/' "$APP" >/dev/null 2>&1; then
  echo "Bundle contains CI runner paths:" >&2
  rg -n '/Users/runner/' "$APP" >&2 || true
  exit 1
fi

if [[ ! -d "$APP/Contents/Resources/site-packages/expando" ]]; then
  echo "Missing bundled site-packages/expando" >&2
  exit 1
fi

if [[ ! -x "$APP/Contents/Frameworks/Python.framework/Versions/"*"/bin/python3" ]]; then
  echo "Missing embedded Python.framework runtime" >&2
  exit 1
fi

"$APP/Contents/MacOS/expando" --version >/dev/null
echo "Distribution bundle verification passed for $APP"