#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/Expando.app/Contents/MacOS/expando"

if [[ -x "$APP" ]]; then
  exec "$APP"
fi

VENV="$ROOT/.venv"
if [[ ! -x "$VENV/bin/expando" ]]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q -e "$ROOT"
fi

exec "$VENV/bin/expando" run