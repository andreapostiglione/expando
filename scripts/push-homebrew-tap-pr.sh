#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DMG="${1:-$ROOT/Expando.dmg}"
TAP_REPO="${EXPANDO_HOMEBREW_TAP_REPO:-andreapostiglione/homebrew-tap}"
TAP_BRANCH="${EXPANDO_HOMEBREW_TAP_BRANCH:-}"
HEAD_BRANCH=""

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

if [[ -n "${GH_TOKEN:-${GITHUB_TOKEN:-}}" ]]; then
  export GH_TOKEN="${GH_TOKEN:-$GITHUB_TOKEN}"
  gh auth setup-git
fi

VERSION="$(python3 - <<'PY'
import tomllib
from pathlib import Path
data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
print(data["project"]["version"])
PY
)"
HEAD_BRANCH="expando-${VERSION}"
SHA256="$(shasum -a 256 "$DMG" | awk '{print $1}')"
OWNER="${TAP_REPO%%/*}"

EXISTING_PR="$(gh pr list --repo "$TAP_REPO" --head "${OWNER}:${HEAD_BRANCH}" --state open --json url --jq '.[0].url' 2>/dev/null || true)"
if [[ -n "$EXISTING_PR" ]]; then
  echo "Homebrew tap PR already open: $EXISTING_PR"
  exit 0
fi

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

git clone --depth 1 --branch "$TAP_BRANCH" "https://github.com/${TAP_REPO}.git" "$WORKDIR/tap"
cd "$WORKDIR/tap"
git checkout -B "$HEAD_BRANCH"

cat > Casks/expando.rb <<EOF
cask "expando" do
  version "${VERSION}"

  sha256 "${SHA256}"

  url "https://github.com/andreapostiglione/expando/releases/download/v#{version}/Expando.dmg",
      verified: "github.com/andreapostiglione/expando/"
  depends_on formula: "python@3.12"
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
if git diff --staged --quiet; then
  echo "Cask already matches ${VERSION}; nothing to commit."
else
  git commit -m "chore(cask): bump expando to ${VERSION}"
fi
git push -u origin "$HEAD_BRANCH" --force-with-lease

gh pr create \
  --repo "$TAP_REPO" \
  --head "$HEAD_BRANCH" \
  --base "$TAP_BRANCH" \
  --title "expando ${VERSION}" \
  --body "Automated cask bump from expando release v${VERSION}."
