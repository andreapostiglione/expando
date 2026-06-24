#!/usr/bin/env bash
set -euo pipefail

# Repairs a broken DMG install when the bundled venv points at CI paths.
# For modern standalone DMG releases, the embedded Python runtime should make this rarely needed.
# Falls back to system Python + site-packages.

APP="${1:-/Applications/Expando.app}"
ROOT="${2:-$(cd "$(dirname "$0")/.." && pwd)}"
RESOURCES="$APP/Contents/Resources"
SITE_PACKAGES="$RESOURCES/site-packages"

if [[ ! -d "$APP/Contents/MacOS" ]]; then
  echo "Expando.app not found at: $APP" >&2
  exit 1
fi

PYTHON=""
# Strongly prefer embedded runtime for standalone DMG repair (no host dep)
for candidate in \
    "$APP/Contents/Resources/python/bin/python3" \
    "$APP/Contents/Resources/python/bin/python"; do
  if [[ -x "$candidate" ]] && "$candidate" -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    PYTHON="$candidate"
    break
  fi
done

if [[ -z "$PYTHON" ]]; then
  # Fallback to host ONLY if no embedded (legacy installs); warn strongly
  for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if [[ -x "$candidate" ]] && "$candidate" -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
      PYTHON="$candidate"
      break
    fi
  done
fi

if [[ -z "$PYTHON" ]]; then
  echo "Python 3.10+ not found (no embedded, no host)." >&2
  echo "Re-download the official standalone DMG from GitHub Releases." >&2
  exit 1
fi

rm -rf "$RESOURCES/venv"
mkdir -p "$SITE_PACKAGES"
"$PYTHON" -m pip install -q "$ROOT" --target "$SITE_PACKAGES" --upgrade --force-reinstall --no-cache-dir

# Install a launcher that prefers embedded if present, else minimal host (for repair of old)
if [[ -f "$ROOT/scripts/distribution-launcher.sh" ]]; then
  cp "$ROOT/scripts/distribution-launcher.sh" "$APP/Contents/MacOS/expando"
else
  cat > "$APP/Contents/MacOS/expando" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
RESOURCES="$APP_DIR/Contents/Resources"
SITE_PACKAGES="$RESOURCES/site-packages"
export PYTHONPATH="$SITE_PACKAGES${PYTHONPATH:+:$PYTHONPATH}"
export EXPANDO_RESOURCES="$RESOURCES"
if [[ $# -eq 0 ]]; then set -- run; fi
PYBIN=""
for c in "$RESOURCES/python/bin/python3" "$RESOURCES/python/bin/python"; do
  if [[ -x "$c" ]]; then PYBIN="$c"; break; fi
done
if [[ -n "$PYBIN" ]]; then exec "$PYBIN" -m expando "$@"; fi
for c in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
  if [[ -x "$c" ]]; then exec "$c" -m expando "$@"; fi
done
osascript -e 'display alert "Expando" message "Embedded Python runtime missing. Reinstall latest DMG."'
exit 1
EOF
fi

chmod +x "$APP/Contents/MacOS/expando"
xattr -dr com.apple.quarantine "$APP" 2>/dev/null || true

echo "Repaired $APP (used $PYTHON; prefer re-download standalone DMG if possible)"
"$APP/Contents/MacOS/expando" --version || true