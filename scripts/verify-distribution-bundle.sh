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

if grep -q '/Users/runner/' "$APP/Contents/MacOS/expando" 2>/dev/null; then
  echo "Launcher contains CI runner paths" >&2
  exit 1
fi

export PYTHONPATH="$APP/Contents/Resources/site-packages${PYTHONPATH:+:$PYTHONPATH}"
python3 -c "from expando.paths import package_root; root = package_root(); assert (root / 'default_config' / 'config' / 'default.yml').is_file(), root; import expando"

"$APP/Contents/MacOS/expando" --version >/dev/null
echo "Distribution bundle verification passed for $APP"
