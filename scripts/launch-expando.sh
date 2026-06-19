#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/Expando.app/Contents/MacOS/expando"
VENV_BIN="$ROOT/.venv/bin/expando"

_ensure_venv() {
  if [[ ! -x "$VENV_BIN" ]]; then
    python3 -m venv "$ROOT/.venv"
    "$ROOT/.venv/bin/pip" install -q -e "$ROOT"
  fi
}

if [[ "${EXPANDO_USE_APP:-}" == "1" ]] && [[ -x "$APP" ]]; then
  exec "$APP"
fi

# Prefer repo venv when present (dev editable install; avoids unsigned .app + Homebrew Python Team ID issues)
if [[ -x "$VENV_BIN" ]]; then
  exec "$VENV_BIN" run
fi

if [[ -x "$APP" ]]; then
  exec "$APP"
fi

_ensure_venv
exec "$VENV_BIN" run