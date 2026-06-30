#!/usr/bin/env bash
set -euo pipefail

APP="${1:?app bundle path required}"
ROOT="${2:?project root required}"

RESOURCES="$APP/Contents/Resources"
SITE_PACKAGES="$RESOURCES/site-packages"
FRAMEWORKS="$APP/Contents/Frameworks"
PYTHON_FRAMEWORK="$FRAMEWORKS/Python.framework"
PYTHON_DYLIB_RPATH="@rpath/Python.framework/Versions/3.12/Python"

_python_is_312() {
  "$1" -c 'import sys; exit(0 if sys.version_info[:2] == (3, 12) else 1)' 2>/dev/null
}

_python_framework_for() {
  "$1" - <<'PY' 2>/dev/null
import sysconfig
from pathlib import Path

path = sysconfig.get_config_var("PYTHONFRAMEWORKINSTALLDIR") or ""
if not path:
    raise SystemExit(1)
framework = Path(path)
if (framework / "Versions" / "3.12" / "Python").is_file():
    print(framework)
    raise SystemExit(0)
raise SystemExit(1)
PY
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
    if [[ -n "$candidate" && -x "$candidate" ]] \
      && _python_is_312 "$candidate" \
      && _python_framework_for "$candidate" >/dev/null; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

_is_macho() {
  file "$1" | grep -q "Mach-O"
}

_macho_files() {
  find "$APP" -type f \( -perm -111 -o -name "*.so" -o -name "*.dylib" -o -name Python -o -name "python3.12" \) -print0 2>/dev/null
}

_is_external_runtime_ref() {
  case "$1" in
    /opt/homebrew/*|/usr/local/*|/Library/Frameworks/Python.framework/*)
      return 0
      ;;
  esac
  return 1
}

_is_python_runtime_ref() {
  case "$1" in
    */Python.framework/Versions/3.12/Python)
      return 0
      ;;
  esac
  return 1
}

_collect_runtime_dylib_refs() {
  _macho_files | while IFS= read -r -d '' candidate; do
    if _is_macho "$candidate"; then
      otool -L "$candidate" 2>/dev/null | awk 'NR > 1 {print $1}'
    fi
  done | while IFS= read -r ref; do
    if _is_external_runtime_ref "$ref" && ! _is_python_runtime_ref "$ref"; then
      printf '%s\n' "$ref"
    fi
  done | sort -u
}

_normalize_python_framework_bundle() {
  mkdir -p "$PYTHON_FRAMEWORK/Versions/3.12/Resources"
  ln -sfn 3.12 "$PYTHON_FRAMEWORK/Versions/Current"
  ln -sfn Versions/Current/Python "$PYTHON_FRAMEWORK/Python"
  ln -sfn Versions/Current/Resources "$PYTHON_FRAMEWORK/Resources"
  cat > "$PYTHON_FRAMEWORK/Versions/3.12/Resources/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>Python</string>
    <key>CFBundleIdentifier</key>
    <string>org.python.python</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Python</string>
    <key>CFBundlePackageType</key>
    <string>FMWK</string>
    <key>CFBundleShortVersionString</key>
    <string>3.12</string>
    <key>CFBundleVersion</key>
    <string>3.12</string>
</dict>
</plist>
EOF
}

_remove_broken_python_framework_symlinks() {
  find "$PYTHON_FRAMEWORK" -type l -print0 | while IFS= read -r -d '' link; do
    if [[ ! -e "$link" ]]; then
      rm -f "$link"
    fi
  done
}

_embed_runtime_dylibs() {
  local refs_file
  refs_file="$(mktemp)"
  _collect_runtime_dylib_refs >"$refs_file"
  while IFS= read -r ref; do
    if [[ -z "$ref" ]]; then
      continue
    fi
    cp -f "$ref" "$FRAMEWORKS/$(basename "$ref")"
    chmod u+w "$FRAMEWORKS/$(basename "$ref")"
  done <"$refs_file"
  rm -f "$refs_file"
}

_rewrite_runtime_links() {
  _macho_files | while IFS= read -r -d '' candidate; do
    if ! _is_macho "$candidate"; then
      continue
    fi
    chmod u+w "$candidate" 2>/dev/null || true
    if [[ "$candidate" == "$PYTHON_FRAMEWORK/Versions/3.12/Python" ]]; then
      install_name_tool -id "$PYTHON_DYLIB_RPATH" "$candidate"
    elif [[ "$candidate" == "$PYTHON_FRAMEWORK/Versions/3.12/bin/python3.12" ]]; then
      if ! otool -l "$candidate" | grep -q '@executable_path/../../../..'; then
        install_name_tool -add_rpath '@executable_path/../../../..' "$candidate"
      fi
    elif [[ "$candidate" == "$PYTHON_FRAMEWORK/Versions/3.12/Resources/Python.app/Contents/MacOS/Python" ]]; then
      if ! otool -l "$candidate" | grep -q '@executable_path/../../../../../../..'; then
        install_name_tool -add_rpath '@executable_path/../../../../../../..' "$candidate"
      fi
    elif [[ "$(dirname "$candidate")" == "$FRAMEWORKS" && "$(basename "$candidate")" == *.dylib ]]; then
      install_name_tool -id "@rpath/$(basename "$candidate")" "$candidate"
    fi
    otool -L "$candidate" 2>/dev/null | awk 'NR > 1 {print $1}' | while IFS= read -r ref; do
      if ! _is_external_runtime_ref "$ref"; then
        continue
      fi
      if _is_python_runtime_ref "$ref"; then
        install_name_tool -change "$ref" "$PYTHON_DYLIB_RPATH" "$candidate"
      else
        install_name_tool -change "$ref" "@rpath/$(basename "$ref")" "$candidate"
      fi
    done
  done
}

_adhoc_sign_runtime() {
  if ! command -v codesign >/dev/null 2>&1; then
    return 0
  fi
  find "$FRAMEWORKS" -type f \( -perm -111 -o -name "*.so" -o -name "*.dylib" -o -name Python -o -name "python3.12" \) -print0 2>/dev/null \
    | while IFS= read -r -d '' candidate; do
        if _is_macho "$candidate"; then
          codesign --force --sign - "$candidate" >/dev/null 2>&1
        fi
      done
}

PY312="$(_find_python312)" || {
  echo "Python 3.12 framework is required for distribution bundling" >&2
  exit 1
}
PYTHON_FRAMEWORK_SRC="$(_python_framework_for "$PY312")"

rm -rf \
  "$SITE_PACKAGES" \
  "$RESOURCES/venv" \
  "$RESOURCES/default_config" \
  "$RESOURCES/packages" \
  "$RESOURCES/scripts" \
  "$PYTHON_FRAMEWORK"
mkdir -p "$SITE_PACKAGES" "$FRAMEWORKS"

"$PY312" -m pip install -q "$ROOT" --target "$SITE_PACKAGES" --no-cache-dir --no-compile
ditto "$PYTHON_FRAMEWORK_SRC" "$PYTHON_FRAMEWORK"
rm -rf \
  "$PYTHON_FRAMEWORK"/Versions/*/_CodeSignature \
  "$PYTHON_FRAMEWORK"/Versions/3.12/lib/python3.12/test
find "$PYTHON_FRAMEWORK" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$PYTHON_FRAMEWORK" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
_normalize_python_framework_bundle
_remove_broken_python_framework_symlinks
_embed_runtime_dylibs
_rewrite_runtime_links
_adhoc_sign_runtime
cp -R "$ROOT/default_config" "$RESOURCES/default_config"
cp -R "$ROOT/packages" "$RESOURCES/packages"
mkdir -p "$RESOURCES/scripts"
for script in \
  com.andreapostiglione.expando.plist \
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
echo "Embedded Python.framework from $PYTHON_FRAMEWORK_SRC"
