#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if [[ "${EXPANDO_CONFIRM_LIVE_E2E:-0}" != "1" ]]; then
  echo "Running headless-safe E2E only. Set EXPANDO_CONFIRM_LIVE_E2E=1 for live TextEdit/keyboard tests." >&2
  pytest tests/e2e -v -m "not clipboard and not image and not integration" "$@"
  exit 0
fi

export EXPANDO_E2E_FULL="${EXPANDO_E2E_FULL:-1}"
export EXPANDO_E2E_TEXTEDIT="${EXPANDO_E2E_TEXTEDIT:-1}"
export EXPANDO_E2E_CLIPBOARD="${EXPANDO_E2E_CLIPBOARD:-1}"
export EXPANDO_E2E_IMAGE="${EXPANDO_E2E_IMAGE:-1}"
pytest tests/e2e -v "$@"
