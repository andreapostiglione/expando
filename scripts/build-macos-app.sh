#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/Expando.app"
MACOS="$APP/Contents/MacOS"
RESOURCES="$APP/Contents/Resources"
VERSION="$(grep '^version' "$ROOT/pyproject.toml" | head -1 | sed 's/.*"\(.*\)".*/\1/')"

mkdir -p "$MACOS" "$RESOURCES"

if [[ "${EXPANDO_DISTRIBUTION:-0}" == "1" ]]; then
  VENV="$RESOURCES/venv"
  rm -rf "$VENV"
  python3 -m venv --copies "$VENV"
  "$VENV/bin/pip" install -q --upgrade pip
  "$VENV/bin/pip" install -q -e "$ROOT"
  LAUNCHER_VENV='$APP_DIR/Contents/Resources/venv/bin/expando'
else
  LAUNCHER_VENV='$ROOT/.venv/bin/expando'
fi

cat > "$MACOS/expando" <<EOF
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="\$(cd "\$(dirname "\$0")/../.." && pwd)"
ROOT="\$(dirname "\$APP_DIR")"
VENV="$LAUNCHER_VENV"

if [[ ! -x "\$VENV" ]]; then
  if [[ -x "\$ROOT/.venv/bin/expando" ]]; then
    VENV="\$ROOT/.venv/bin/expando"
  else
    python3 -m venv "\$ROOT/.venv"
    "\$ROOT/.venv/bin/pip" install -q -e "\$ROOT"
    VENV="\$ROOT/.venv/bin/expando"
  fi
fi

exec "\$VENV" run "\$@"
EOF

chmod +x "$MACOS/expando"

cat > "$APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>expando</string>
    <key>CFBundleIdentifier</key>
    <string>com.andreapostiglione.expando</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Expando</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>${VERSION}</string>
    <key>CFBundleVersion</key>
    <string>${VERSION}</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

echo "Built $APP (v${VERSION}, distribution=${EXPANDO_DISTRIBUTION:-0})"
if [[ "${EXPANDO_DISTRIBUTION:-0}" != "1" ]]; then
  echo "Grant Accessibility permission to Expando.app (not python3.14)"
fi