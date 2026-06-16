#!/usr/bin/env bash
# Configure GitHub Actions secrets for signed + notarized DMG releases.
# Run from repo root. Requires: gh auth login, Keychain access, Apple app-specific password.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

IDENTITY="${APPLE_SIGNING_IDENTITY:-Developer ID Application: Inochi Srl (68Q8CQBQQV)}"
TEAM_ID="${NOTARY_TEAM_ID:-68Q8CQBQQV}"
APPLE_ID="${NOTARY_APPLE_ID:-andreapostiglione@live.it}"
P12_PATH="${APPLE_P12_PATH:-$ROOT/.release-certificate.p12}"

echo "==> Expando — GitHub release secrets"
echo "Identity: $IDENTITY"
echo "Team ID:  $TEAM_ID"
echo "Apple ID: $APPLE_ID"
echo

if ! command -v gh >/dev/null; then
  echo "Install GitHub CLI: brew install gh && gh auth login" >&2
  exit 1
fi

KEYCHAIN="${HOME}/Library/Keychains/login.keychain-db"

if [[ ! -f "$P12_PATH" ]]; then
  if ! security find-identity -v -p codesigning | grep -Fq "$IDENTITY"; then
    echo "Signing identity not found in Keychain: $IDENTITY" >&2
    security find-identity -v -p codesigning >&2
    exit 1
  fi

  echo "Exporting signing identities to $P12_PATH"
  echo "(macOS may prompt for your Mac login password — this is normal)"
  read -r -s -p "Choose a password to protect the .p12 file: " P12_PASSWORD
  echo
  # security export does not support -c; export all code-signing identities.
  security export -k "$KEYCHAIN" -t identities -f pkcs12 \
    -o "$P12_PATH" -P "$P12_PASSWORD"
else
  read -r -s -p "Password for existing $P12_PATH: " P12_PASSWORD
  echo
fi

read -r -s -p "Apple app-specific password (for notarization): " NOTARY_PASSWORD
echo

CERT_B64="$(base64 < "$P12_PATH" | tr -d '\n')"

gh secret set APPLE_CERTIFICATE_BASE64 --body "$CERT_B64"
gh secret set APPLE_CERTIFICATE_PASSWORD --body "$P12_PASSWORD"
gh secret set APPLE_SIGNING_IDENTITY --body "$IDENTITY"
gh secret set NOTARY_APPLE_ID --body "$APPLE_ID"
gh secret set NOTARY_PASSWORD --body "$NOTARY_PASSWORD"
gh secret set NOTARY_TEAM_ID --body "$TEAM_ID"

echo
echo "Done. Secrets configured:"
gh secret list
echo
echo "Optional — local notary keychain profile:"
echo "  xcrun notarytool store-credentials expando-notary \\"
echo "    --apple-id \"$APPLE_ID\" --team-id \"$TEAM_ID\" --password \"<app-specific-password>\""
echo
echo "Test CI: git tag v1.2.2 && git push origin v1.2.2"