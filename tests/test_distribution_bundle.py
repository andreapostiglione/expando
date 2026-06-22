from pathlib import Path


def test_distribution_launcher_defaults_to_run() -> None:
    launcher = Path(__file__).resolve().parents[1] / "scripts" / "distribution-launcher.sh"
    text = launcher.read_text(encoding="utf-8")
    assert 'set -- run' in text
    assert "-m expando" in text


def test_verify_distribution_bundle_script_exists() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "verify-distribution-bundle.sh"
    assert script.is_file()