import subprocess
from pathlib import Path


def test_distribution_launcher_defaults_to_run() -> None:
    launcher = Path(__file__).resolve().parents[1] / "scripts" / "distribution-launcher.sh"
    text = launcher.read_text(encoding="utf-8")
    assert 'set -- run' in text
    assert "-m expando" in text


def test_verify_distribution_bundle_script_exists() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "verify-distribution-bundle.sh"
    assert script.is_file()


def test_distribution_bundle_scripts_verify_runtime_assets() -> None:
    root = Path(__file__).resolve().parents[1]
    embed = (root / "scripts" / "embed-distribution-python.sh").read_text(encoding="utf-8")
    verify = (root / "scripts" / "verify-distribution-bundle.sh").read_text(encoding="utf-8")

    assert "$RESOURCES/default_config" in embed
    assert "$RESOURCES/packages" in embed
    assert "default_config/config/default.yml" in verify
    assert "packages/hub/index.json" in verify


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


def test_appcast_generation_requires_sparkle_signature() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "generate-appcast.sh"
    text = script.read_text(encoding="utf-8")

    assert "SPARKLE_PRIVATE_KEY is required" in text
    assert "sparkle:edSignature" in text


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
