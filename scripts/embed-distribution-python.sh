#!/usr/bin/env bash
set -euo pipefail

APP="${1:?app bundle path required}"
ROOT="${2:?project root required}"

RESOURCES="$APP/Contents/Resources"
SITE_PACKAGES="$RESOURCES/site-packages"
FRAMEWORK_SRC="/Library/Frameworks/Python.framework"
FRAMEWORK_DST="$APP/Contents/Frameworks/Python.framework"

if [[ ! -d "$FRAMEWORK_SRC" ]]; then
  echo "Python.framework not found at $FRAMEWORK_SRC." >&2
  echo "Distribution builds require python.org framework Python on the build host." >&2
  exit 1
fi

PY_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
FW_PREFIX="/Library/Frameworks/Python.framework/Versions/$PY_VERSION"

rm -rf "$FRAMEWORK_DST" "$SITE_PACKAGES" "$RESOURCES/venv"
mkdir -p "$SITE_PACKAGES"
ditto "$FRAMEWORK_SRC" "$FRAMEWORK_DST"

patch_python_ref() {
  local binary="$1"
  [[ -f "$binary" ]] || return 0
  file "$binary" 2>/dev/null | grep -q "Mach-O" || return 0
  install_name_tool -change \
    "$FW_PREFIX/Python" \
    "@loader_path/../Python" \
    "$binary" 2>/dev/null || true
}

FW_VERSION_DIR="$FRAMEWORK_DST/Versions/$PY_VERSION"
install_name_tool -id "@loader_path/Python" "$FW_VERSION_DIR/Python" 2>/dev/null || true

for binary in \
  "$FW_VERSION_DIR/bin/python3" \
  "$FW_VERSION_DIR/bin/python3.$PY_VERSION" \
  "$FW_VERSION_DIR/Python" \
  "$FW_VERSION_DIR/Resources/Python.app/Contents/MacOS/Python"; do
  patch_python_ref "$binary"
done

EMBEDDED_PY="$FW_VERSION_DIR/bin/python3"
"$EMBEDDED_PY" -m pip install -q --upgrade pip
"$EMBEDDED_PY" -m pip install -q "$ROOT" --target "$SITE_PACKAGES"

while IFS= read -r -d '' shared_object; do
  patch_python_ref "$shared_object"
done < <(find "$SITE_PACKAGES" -type f \( -name "*.so" -o -name "*.dylib" \) -print0 2>/dev/null)

echo "Embedded Python $PY_VERSION into $APP"