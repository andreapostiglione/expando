#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/Expando.app"
MACOS="$APP/Contents/MacOS"
RESOURCES="$APP/Contents/Resources"

mkdir -p "$MACOS" "$RESOURCES"

cat > "$MACOS/expando" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
ROOT="$(dirname "$APP_DIR")"
VENV="$ROOT/.venv"

if [[ ! -x "$VENV/bin/expando" ]]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q -e "$ROOT"
fi

exec "$VENV/bin/expando" run "$@"
EOF

chmod +x "$MACOS/expando"

cat > "$APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>it</string>
    <key>CFBundleExecutable</key>
    <string>expando</string>
    <key>CFBundleIdentifier</key>
    <string>com.inochisrl.expando</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Expando</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>0.2.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

echo "Built $APP"
echo "Concedi i permessi Privacy a Expando.app (non python3.14)"