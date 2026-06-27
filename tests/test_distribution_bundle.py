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
