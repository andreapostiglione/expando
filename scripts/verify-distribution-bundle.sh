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

if grep -q '/Users/runner/' "$APP/Contents/MacOS/expando" 2>/dev/null; then
  echo "Launcher contains CI runner paths" >&2
  exit 1
fi

export PYTHONPATH="$APP/Contents/Resources/site-packages${PYTHONPATH:+:$PYTHONPATH}"
python3 -c "import expando"

"$APP/Contents/MacOS/expando" --version >/dev/null
echo "Distribution bundle verification passed for $APP"