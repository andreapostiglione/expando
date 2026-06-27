#!/usr/bin/env bash
# Configure GitHub Actions secrets for signed + notarized DMG releases.
# Run from repo root. Requires: gh auth login, Keychain access, Apple app-specific password.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

IDENTITY="${APPLE_SIGNING_IDENTITY:-}"
TEAM_ID="${NOTARY_TEAM_ID:-}"
APPLE_ID="${NOTARY_APPLE_ID:-}"
P12_PATH="${APPLE_P12_PATH:-$ROOT/.release-certificate.p12}"

if [[ -z "$IDENTITY" || -z "$TEAM_ID" || -z "$APPLE_ID" ]]; then
  echo "Set APPLE_SIGNING_IDENTITY, NOTARY_TEAM_ID, and NOTARY_APPLE_ID before running." >&2
  exit 1
fi

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
if [[ -z "$NOTARY_PASSWORD" ]]; then
  echo "App-specific password is required for notarization." >&2
  exit 1
fi

CERT_B64="$(base64 < "$P12_PATH" | tr -d '\n')"

gh secret set APPLE_CERTIFICATE_BASE64 --body "$CERT_B64"
gh secret set APPLE_CERTIFICATE_PASSWORD --body "$P12_PASSWORD"
gh secret set APPLE_SIGNING_IDENTITY --body "$IDENTITY"
gh secret set NOTARY_APPLE_ID --body "$APPLE_ID"
gh secret set NOTARY_PASSWORD --body "$NOTARY_PASSWORD"
gh secret set NOTARY_TEAM_ID --body "$TEAM_ID"

if [[ -n "${EXPANDO_SPARKLE_PUBLIC_ED_KEY:-}" ]]; then
  gh secret set EXPANDO_SPARKLE_PUBLIC_ED_KEY --body "$EXPANDO_SPARKLE_PUBLIC_ED_KEY"
else
  echo "EXPANDO_SPARKLE_PUBLIC_ED_KEY not set; add it before production releases." >&2
fi
if [[ -n "${SPARKLE_PRIVATE_KEY:-}" ]]; then
  gh secret set SPARKLE_PRIVATE_KEY --body "$SPARKLE_PRIVATE_KEY"
else
  echo "SPARKLE_PRIVATE_KEY not set; add it before production releases." >&2
fi

echo
echo "Done. Secrets configured:"
gh secret list
echo
echo "Optional — local notary keychain profile:"
echo "  xcrun notarytool store-credentials expando-notary \\"
echo "    --apple-id \"$APPLE_ID\" --team-id \"$TEAM_ID\" --password \"<app-specific-password>\""
echo
echo "Test CI: git tag v1.2.2 && git push origin v1.2.2"
