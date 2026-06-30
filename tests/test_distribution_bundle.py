import subprocess
from pathlib import Path


def test_native_distribution_launcher_defaults_to_run() -> None:
    launcher = Path(__file__).resolve().parents[1] / "scripts" / "expando-launcher.c"
    text = launcher.read_text(encoding="utf-8")
    assert 'python_argv[3] = "run"' in text
    assert 'EXPANDO_PYTHON_VERSION "3.12"' in text
    assert "Py_BytesMain" in text
    assert 'python_argv[1] = "-m"' in text
    assert 'python_argv[2] = "expando"' in text


def test_verify_distribution_bundle_script_exists() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "verify-distribution-bundle.sh"
    assert script.is_file()


def test_distribution_bundle_scripts_verify_runtime_assets() -> None:
    root = Path(__file__).resolve().parents[1]
    embed = (root / "scripts" / "embed-distribution-python.sh").read_text(encoding="utf-8")
    verify = (root / "scripts" / "verify-distribution-bundle.sh").read_text(encoding="utf-8")
    native_launcher = (root / "scripts" / "expando-launcher.c").read_text(encoding="utf-8")
    build = (root / "scripts" / "build-macos-app.sh").read_text(encoding="utf-8")

    assert "$RESOURCES/default_config" in embed
    assert "$RESOURCES/packages" in embed
    assert "--no-compile" in embed
    assert "Python 3.12 framework is required for distribution bundling" in embed
    assert "Embedded Python.framework" in embed
    assert "_normalize_python_framework_bundle" in embed
    assert "_remove_broken_python_framework_symlinks" in embed
    assert "CFBundlePackageType" in embed
    assert "_embed_runtime_dylibs" in embed
    assert "install_name_tool -change" in embed
    assert "install_name_tool -add_rpath" in embed
    assert "PYTHON_DYLIB_RPATH" in embed
    assert "_adhoc_sign_runtime" in embed
    assert '"$PY312" -m pip install' in embed
    assert "find \"$SITE_PACKAGES\" -type d -name __pycache__" in embed
    assert "setenv(\"PYTHONDONTWRITEBYTECODE\"" in native_launcher
    assert "/opt/homebrew/opt/python@3.12" not in native_launcher
    assert "/usr/local/opt/python@3.12" not in native_launcher
    assert "/Library/Frameworks/Python.framework" not in native_launcher
    assert "expando-launcher.c" in build
    assert "-Wl,-rpath,@executable_path/../Frameworks" in build
    assert "Distribution launcher must be a native Mach-O executable" in verify
    assert "Missing embedded Python.framework runtime" in verify
    assert "Embedded Python.framework is missing bundle metadata" in verify
    assert "Bundle contains local dynamic library references" in verify
    assert "PYTHONDONTWRITEBYTECODE=1" in verify
    assert "default_config/config/default.yml" in verify
    assert "packages/hub/index.json" in verify
    assert "python3.12 is required to verify bundled native dependencies" in verify
    assert "from pynput import keyboard" in verify
    assert "import ssl" in verify
    assert "import sqlite3" in verify
    assert "Native launcher failed to start the keyboard listener" in verify


def test_bundled_launch_agent_script_uses_app_executable(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    app = tmp_path / "Expando.app"
    resources_scripts = app / "Contents" / "Resources" / "scripts"
    macos = app / "Contents" / "MacOS"
    resources_scripts.mkdir(parents=True)
    macos.mkdir(parents=True)

    launch_script = resources_scripts / "launch-expando.sh"
    launch_script.write_text(
        (root / "scripts" / "launch-expando.sh").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    launch_script.chmod(0o755)

    output = tmp_path / "launched.txt"
    app_executable = macos / "expando"
    app_executable.write_text(
        f"#!/usr/bin/env bash\nprintf '%s\\n' \"$0\" \"$@\" > {output}\n",
        encoding="utf-8",
    )
    app_executable.chmod(0o755)

    subprocess.run(["bash", str(launch_script)], check=True, timeout=10)

    launched = output.read_text(encoding="utf-8").splitlines()
    assert Path(launched[0]).resolve() == app_executable.resolve()
    assert not (app / "Contents" / "Resources" / ".venv").exists()


def test_distribution_build_requires_sparkle_public_key() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "build-macos-app.sh"
    text = script.read_text(encoding="utf-8")

    assert "EXPANDO_SPARKLE_PUBLIC_ED_KEY" in text
    assert "SUPublicEDKey" in text


def test_codesign_preserves_launcher_entitlements() -> None:
    root = Path(__file__).resolve().parents[1]
    script = (root / "scripts" / "codesign-app.sh").read_text(encoding="utf-8")
    entitlements = (root / "scripts" / "entitlements.plist").read_text(encoding="utf-8")

    launcher_sign = (
        'codesign --force --options runtime --timestamp \\\n'
        '  --entitlements "$ENTITLEMENTS" \\\n'
        '  --sign "$IDENTITY" "$APP/Contents/MacOS/expando"'
    )
    assert launcher_sign in script
    assert 'find "$APP/Contents/Frameworks" -type d -name "*.framework"' in script
    assert "com.apple.security.cs.disable-library-validation" not in entitlements
    assert "com.apple.security.automation.apple-events" in entitlements


def test_appcast_generation_requires_sparkle_signature() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "generate-appcast.sh"
    text = script.read_text(encoding="utf-8")

    assert "SPARKLE_PRIVATE_KEY is required" in text
    assert "sparkle:edSignature" in text


def test_sparkle_helper_links_with_bundle_rpath() -> None:
    root = Path(__file__).resolve().parents[1]
    embed = (root / "scripts" / "embed-sparkle.sh").read_text(encoding="utf-8")
    verify = (root / "scripts" / "verify-distribution-bundle.sh").read_text(encoding="utf-8")

    assert "-Wl,-rpath,@executable_path/../Frameworks" in embed
    assert "Sparkle helper is missing @executable_path/../Frameworks rpath" in verify


def test_dmg_build_signs_container_before_notarization() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "build-dmg.sh"
    text = script.read_text(encoding="utf-8")

    assert 'codesign --force --timestamp --sign "$IDENTITY" "$DMG"' in text
    assert 'codesign --verify --verbose=2 "$DMG"' in text
    assert text.index('codesign --verify --verbose=2 "$DMG"') < text.index("notarize-dmg.sh")


def test_homebrew_cask_generators_include_verified_url() -> None:
    root = Path(__file__).resolve().parents[1]
    bump = (root / "scripts" / "bump-homebrew-cask.sh").read_text(encoding="utf-8")
    tap_pr = (root / "scripts" / "push-homebrew-tap-pr.sh").read_text(encoding="utf-8")

    assert 'verified: "github.com/andreapostiglione/expando/"' in bump
    assert 'verified: "github.com/andreapostiglione/expando/"' in tap_pr
    assert 'depends_on formula: "python@3.12"' not in bump
    assert 'depends_on formula: "python@3.12"' not in tap_pr
