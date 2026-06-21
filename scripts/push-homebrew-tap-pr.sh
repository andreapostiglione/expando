#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DMG="${1:-$ROOT/Expando.dmg}"
TAP_REPO="${EXPANDO_HOMEBREW_TAP_REPO:-andreapostiglione/homebrew-tap}"
TAP_BRANCH="${EXPANDO_HOMEBREW_TAP_BRANCH:-}"

if [[ -z "$TAP_BRANCH" ]]; then
  TAP_BRANCH="$(gh api "repos/${TAP_REPO}" --jq '.default_branch' 2>/dev/null || true)"
fi
TAP_BRANCH="${TAP_BRANCH:-master}"

if [[ ! -f "$DMG" ]]; then
  echo "DMG not found: $DMG" >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required to open the Homebrew tap PR." >&2
  exit 1
fi

VERSION="$(python3 - <<'PY'
import tomllib
from pathlib import Path
data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
print(data["project"]["version"])
PY
)"
SHA256="$(shasum -a 256 "$DMG" | awk '{print $1}')"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

git clone --depth 1 --branch "$TAP_BRANCH" "https://github.com/${TAP_REPO}.git" "$WORKDIR/tap"
cd "$WORKDIR/tap"
git checkout -b "expando-${VERSION}"

cat > Casks/expando.rb <<EOF
cask "expando" do
  version "${VERSION}"

  sha256 "${SHA256}"

  url "https://github.com/andreapostiglione/expando/releases/download/v#{version}/Expando.dmg"
  name "Expando"
  desc "Privacy-first open-source text expander for macOS"
  homepage "https://andreapostiglione.github.io/expando/"

  app "Expando.app"

  zap trash: [
    "~/Library/Application Support/expando",
  ]
end
EOF

git add Casks/expando.rb
git commit -m "chore(cask): bump expando to ${VERSION}"
git push origin "expando-${VERSION}"

gh pr create \
  --repo "$TAP_REPO" \
  --head "expando-${VERSION}" \
  --base "$TAP_BRANCH" \
  --title "expando ${VERSION}" \
  --body "Automated cask bump from expando release v${VERSION}."