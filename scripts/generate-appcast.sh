#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="${1:-}"
DMG="${2:-$ROOT/Expando.dmg}"
OUTPUT="${3:-$ROOT/appcast.xml}"
NOTES="${4:-}"

if [[ -z "$VERSION" ]]; then
  VERSION="$(grep '^version' "$ROOT/pyproject.toml" | head -1 | sed 's/.*"\(.*\)".*/\1/')"
fi

if [[ ! -f "$DMG" ]]; then
  echo "DMG not found: $DMG" >&2
  exit 1
fi

if stat -f%z "$DMG" >/dev/null 2>&1; then
  LENGTH="$(stat -f%z "$DMG")"
else
  LENGTH="$(stat -c%s "$DMG")"
fi

DOWNLOAD_URL="https://github.com/andreapostiglione/expando/releases/download/v${VERSION}/Expando.dmg"
PUB_DATE="$(date -u '+%a, %d %b %Y %H:%M:%S +0000')"
SIGNATURE_ATTR=""

if [[ -n "${SPARKLE_PRIVATE_KEY:-}" ]]; then
  SPARKLE_VERSION="${SPARKLE_VERSION:-2.6.4}"
  SPARKLE_DIR="$ROOT/.sparkle-tools"
  if [[ ! -x "$SPARKLE_DIR/bin/sign_update" ]]; then
    mkdir -p "$SPARKLE_DIR"
    curl -fsSL "https://github.com/sparkle-project/Sparkle/releases/download/${SPARKLE_VERSION}/Sparkle-${SPARKLE_VERSION}.tar.xz" \
      -o "$SPARKLE_DIR/sparkle.tar.xz"
    tar -xJf "$SPARKLE_DIR/sparkle.tar.xz" -C "$SPARKLE_DIR"
  fi
  KEY_FILE="$SPARKLE_DIR/ed_private_key.pem"
  printf '%s' "$SPARKLE_PRIVATE_KEY" > "$KEY_FILE"
  SIGN_OUTPUT="$("$SPARKLE_DIR/bin/sign_update" -f "$KEY_FILE" "$DMG")"
  ED_SIGNATURE="$(echo "$SIGN_OUTPUT" | sed -n 's/.*edSignature="\([^"]*\)".*/\1/p')"
  if [[ -n "$ED_SIGNATURE" ]]; then
    SIGNATURE_ATTR=" sparkle:edSignature=\"${ED_SIGNATURE}\""
  fi
fi

if [[ -z "$NOTES" ]]; then
  NOTES="Expando ${VERSION} — see GitHub release notes for details."
fi

cat > "$OUTPUT" <<EOF
<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>Expando</title>
    <link>https://github.com/andreapostiglione/expando</link>
    <description>Expando macOS updates (Sparkle appcast)</description>
    <language>en</language>
    <item>
      <title>Version ${VERSION}</title>
      <sparkle:version>${VERSION}</sparkle:version>
      <sparkle:shortVersionString>${VERSION}</sparkle:shortVersionString>
      <description><![CDATA[${NOTES}]]></description>
      <pubDate>${PUB_DATE}</pubDate>
      <enclosure url="${DOWNLOAD_URL}"${SIGNATURE_ATTR} length="${LENGTH}" type="application/octet-stream"/>
    </item>
  </channel>
</rss>
EOF

echo "Wrote $OUTPUT for v${VERSION} (${LENGTH} bytes)"