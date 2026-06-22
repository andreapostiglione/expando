#!/usr/bin/env bash
set -euo pipefail

# Repairs a broken DMG install when the bundled venv points at CI paths.
# Uses system Python 3.10+ and bundled site-packages inside the .app.

APP="${1:-/Applications/Expando.app}"
ROOT="${2:-$(cd "$(dirname "$0")/.." && pwd)}"
RESOURCES="$APP/Contents/Resources"
SITE_PACKAGES="$RESOURCES/site-packages"

if [[ ! -d "$APP/Contents/MacOS" ]]; then
  echo "Expando.app not found at: $APP" >&2
  exit 1
fi

PYTHON=""
for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
  if [[ -x "$candidate" ]] && "$candidate" -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    PYTHON="$candidate"
    break
  fi
done

if [[ -z "$PYTHON" ]]; then
  echo "Python 3.10+ not found. Install Homebrew Python or use a fixed DMG release." >&2
  exit 1
fi

rm -rf "$RESOURCES/venv"
mkdir -p "$SITE_PACKAGES"
"$PYTHON" -m pip install -q "$ROOT" --target "$SITE_PACKAGES" --upgrade --force-reinstall --no-cache-dir

cat > "$APP/Contents/MacOS/expando" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
RESOURCES="$APP_DIR/Contents/Resources"
SITE_PACKAGES="$RESOURCES/site-packages"
export PYTHONPATH="$SITE_PACKAGES${PYTHONPATH:+:$PYTHONPATH}"

if [[ $# -eq 0 ]]; then
  set -- run
fi

FRAMEWORK_VERSIONS="$APP_DIR/Contents/Frameworks/Python.framework/Versions"
if [[ -d "$FRAMEWORK_VERSIONS" ]]; then
  for py in "$FRAMEWORK_VERSIONS"/*/bin/python3; do
    if [[ -x "$py" ]]; then
      exec "$py" -m expando "$@"
    fi
  done
fi

for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
  if [[ -x "$candidate" ]] && "$candidate" -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    exec "$candidate" -m expando "$@"
  fi
done

osascript -e 'display alert "Expando" message "Python 3.10+ is required to run Expando."'
exit 1
EOF

chmod +x "$APP/Contents/MacOS/expando"
xattr -dr com.apple.quarantine "$APP" 2>/dev/null || true

echo "Repaired $APP using $PYTHON"
"$APP/Contents/MacOS/expando" --version