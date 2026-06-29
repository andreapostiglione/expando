#!/usr/bin/env bash
set -euo pipefail

APP="${1:?app bundle path required}"
ROOT="${2:?project root required}"

RESOURCES="$APP/Contents/Resources"
SITE_PACKAGES="$RESOURCES/site-packages"

_python_is_312() {
  "$1" -c 'import sys; exit(0 if sys.version_info[:2] == (3, 12) else 1)' 2>/dev/null
}

_find_python312() {
  for candidate in \
    "${EXPANDO_BUILD_PYTHON312:-}" \
    /opt/homebrew/opt/python@3.12/bin/python3.12 \
    /opt/homebrew/bin/python3.12 \
    /usr/local/opt/python@3.12/bin/python3.12 \
    /usr/local/bin/python3.12 \
    /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 \
    "$(command -v python3.12 2>/dev/null || true)"
  do
    if [[ -n "$candidate" && -x "$candidate" ]] && _python_is_312 "$candidate"; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

PY312="$(_find_python312)" || {
  echo "python3.12 is required for distribution dependency bundling" >&2
  exit 1
}

rm -rf \
  "$SITE_PACKAGES" \
  "$RESOURCES/venv" \
  "$RESOURCES/default_config" \
  "$RESOURCES/packages" \
  "$RESOURCES/scripts" \
  "$APP/Contents/Frameworks/Python.framework"
mkdir -p "$SITE_PACKAGES"

"$PY312" -m pip install -q "$ROOT" --target "$SITE_PACKAGES" --no-cache-dir --no-compile
cp -R "$ROOT/default_config" "$RESOURCES/default_config"
cp -R "$ROOT/packages" "$RESOURCES/packages"
mkdir -p "$RESOURCES/scripts"
for script in \
  com.andreapostiglione.expando.plist \
  distribution-launcher.sh \
  entitlements.plist \
  install-launch-agent.sh \
  launch-expando.sh \
  uninstall-launch-agent.sh
do
  cp "$ROOT/scripts/$script" "$RESOURCES/scripts/$script"
done
chmod +x "$RESOURCES/scripts/"*.sh

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$SITE_PACKAGES" "$PY312" -c "from expando.paths import package_root; root = package_root(); assert (root / 'default_config' / 'config' / 'default.yml').is_file(), root; import expando; print(expando.__version__)"
find "$SITE_PACKAGES" -type d -name __pycache__ -prune -exec rm -rf {} +
echo "Bundled expando into $SITE_PACKAGES with $PY312"
