#!/usr/bin/env bash
set -euo pipefail

APP="${1:?app bundle path required}"
ROOT="${2:?project root required}"

RESOURCES="$APP/Contents/Resources"
SITE_PACKAGES="$RESOURCES/site-packages"

rm -rf \
  "$SITE_PACKAGES" \
  "$RESOURCES/venv" \
  "$RESOURCES/default_config" \
  "$RESOURCES/packages" \
  "$RESOURCES/scripts" \
  "$APP/Contents/Frameworks/Python.framework"
mkdir -p "$SITE_PACKAGES"

python3 -m pip install -q "$ROOT" --target "$SITE_PACKAGES" --no-cache-dir --no-compile
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

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$SITE_PACKAGES" python3 -c "from expando.paths import package_root; root = package_root(); assert (root / 'default_config' / 'config' / 'default.yml').is_file(), root; import expando; print(expando.__version__)"
find "$SITE_PACKAGES" -type d -name __pycache__ -prune -exec rm -rf {} +
echo "Bundled expando into $SITE_PACKAGES"
