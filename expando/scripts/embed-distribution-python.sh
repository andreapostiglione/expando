#!/usr/bin/env bash
set -euo pipefail

# Embed a fully self-contained Python runtime + expando for DMG standalone use.
# No host Python required after installing the app.
# Uses python-build-standalone (https://github.com/indygreg/python-build-standalone)
# for a relocatable interpreter.

APP="${1:?app bundle path required}"
ROOT="${2:?project root required}"

RESOURCES="$APP/Contents/Resources"
SITE_PACKAGES="$RESOURCES/site-packages"
PYTHON_DIR="$RESOURCES/python"
CACHE_DIR="${ROOT}/.python-standalone"

# Clean previous
rm -rf "$SITE_PACKAGES" "$RESOURCES/venv" "$APP/Contents/Frameworks/Python.framework" "$PYTHON_DIR"
mkdir -p "$SITE_PACKAGES" "$PYTHON_DIR" "$CACHE_DIR"

# Python version for embedding (must be >=3.10). Overridable via env for flexibility.
# Defaults to a known recent stable build; script remains self-contained.
# ARCH auto-detected for arm64 (Apple Silicon) / x86_64 (Intel) to avoid brittle hardcodes.
PY_VERSION="${PY_VERSION:-3.12.7}"
PY_BUILD_DATE="${PY_BUILD_DATE:-20241016}"
if [[ -z "${PY_ARCH:-}" ]]; then
  UNAME_M=$(uname -m)
  if [[ "$UNAME_M" == "arm64" || "$UNAME_M" == "aarch64" ]]; then
    PY_ARCH="aarch64-apple-darwin"
  else
    PY_ARCH="x86_64-apple-darwin"
  fi
fi
PY_TARBALL="cpython-${PY_VERSION}+${PY_BUILD_DATE}-${PY_ARCH}-install_only.tar.gz"
PY_URL="https://github.com/indygreg/python-build-standalone/releases/download/${PY_BUILD_DATE}/${PY_TARBALL}"
PY_CACHE="$CACHE_DIR/${PY_TARBALL}"

if [[ ! -f "$PY_CACHE" ]]; then
  echo "Downloading standalone Python ${PY_VERSION} for embedding..."
  curl -fsSL "$PY_URL" -o "$PY_CACHE" || {
    echo "Failed to download embedded Python. Check network or update PY_URL in embed script." >&2
    exit 1
  }
fi

echo "Extracting embedded Python..."
tar -xzf "$PY_CACHE" -C "$CACHE_DIR"
# The tar contains a top-level "python/" dir
if [[ -d "$CACHE_DIR/python" ]]; then
  rm -rf "$PYTHON_DIR"
  mv "$CACHE_DIR/python" "$PYTHON_DIR"
else
  echo "Unexpected tar layout in standalone Python" >&2
  exit 1
fi

# Use the embedded python for installation (fully self contained)
EMBEDDED_PYTHON="$PYTHON_DIR/bin/python3"
if [[ ! -x "$EMBEDDED_PYTHON" ]]; then
  EMBEDDED_PYTHON=$(find "$PYTHON_DIR/bin" -name 'python3*' -perm +111 | head -1)
fi
if [[ ! -x "$EMBEDDED_PYTHON" ]]; then
  echo "No executable python in embedded distribution" >&2
  exit 1
fi

echo "Installing expando + deps into bundled site-packages using embedded Python..."
"$EMBEDDED_PYTHON" -m pip install -q --no-cache-dir --upgrade pip
"$EMBEDDED_PYTHON" -m pip install -q --no-cache-dir --target "$SITE_PACKAGES" "$ROOT"

# Verify
PYTHONPATH="$SITE_PACKAGES" "$EMBEDDED_PYTHON" -c "
import sys
import expando
print('Embedded Python:', sys.version.split()[0])
print('Expando version:', expando.__version__)
print('Bundled successfully.')
"

echo "Python runtime + expando embedded for standalone DMG use."
echo "  Python dir : $PYTHON_DIR"
echo "  Site pkgs  : $SITE_PACKAGES"