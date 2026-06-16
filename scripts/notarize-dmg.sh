#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DMG="${1:-$ROOT/Expando.dmg}"
PROFILE="${NOTARY_KEYCHAIN_PROFILE:-expando-notary}"
TEAM_ID="${NOTARY_TEAM_ID:-68Q8CQBQQV}"

if [[ ! -f "$DMG" ]]; then
  echo "DMG not found: $DMG" >&2
  exit 1
fi

notary_args=(submit "$DMG" --wait)

if [[ -n "${NOTARY_API_KEY:-}" && -n "${NOTARY_API_KEY_ID:-}" && -n "${NOTARY_API_ISSUER:-}" ]]; then
  notary_args+=(--key "$NOTARY_API_KEY" --key-id "$NOTARY_API_KEY_ID" --issuer "$NOTARY_API_ISSUER")
elif [[ -n "${NOTARY_APPLE_ID:-}" && -n "${NOTARY_PASSWORD:-}" ]]; then
  notary_args+=(--apple-id "$NOTARY_APPLE_ID" --password "$NOTARY_PASSWORD" --team-id "$TEAM_ID")
else
  notary_args+=(--keychain-profile "$PROFILE")
fi

echo "Submitting $DMG to Apple notary service..."
xcrun notarytool "${notary_args[@]}"

xcrun stapler staple "$DMG"
xcrun stapler validate "$DMG"

echo "Notarized and stapled: $DMG"