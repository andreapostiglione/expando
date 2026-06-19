#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(python3 - <<'PY'
import tomllib
from pathlib import Path
data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
print(data["project"]["version"])
PY
)"
DMG="${1:-$ROOT/Expando.dmg}"

if [[ ! -f "$DMG" ]]; then
  echo "DMG not found: $DMG" >&2
  exit 1
fi

SHA256="$(shasum -a 256 "$DMG" | awk '{print $1}')"

cat <<EOF
# Homebrew cask bump for Expando ${VERSION}
cask "expando" do
  version "${VERSION}"
  sha256 "${SHA256}"
  url "https://github.com/andreapostiglione/expando/releases/download/v${VERSION}/Expando.dmg"
end
EOF