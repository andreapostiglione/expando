from pathlib import Path
from unittest.mock import patch

from expando.sparkle_native import (
    SparkleSmokeReport,
    format_sparkle_smoke_report,
    smoke_test_sparkle_embed,
)


def test_smoke_test_fails_without_embeds(tmp_path: Path):
    bundle = tmp_path / "Expando.app"
    bundle.mkdir()
    report = smoke_test_sparkle_embed(bundle)
    assert report.ok is False
    assert report.framework_present is False
    assert report.helper_path is None
    assert len(report.errors) >= 2


def test_smoke_test_passes_with_helper_and_framework(tmp_path: Path):
    bundle = tmp_path / "Expando.app"
    helper = bundle / "Contents" / "MacOS" / "expando-sparkle"
    framework = bundle / "Contents" / "Frameworks" / "Sparkle.framework"
    helper.parent.mkdir(parents=True)
    framework.mkdir(parents=True)
    helper.write_text("", encoding="utf-8")
    helper.chmod(0o755)

    with patch("subprocess.run", return_value=type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()):
        report = smoke_test_sparkle_embed(bundle)

    assert report.ok is True
    assert report.framework_present is True
    assert report.helper_path is not None


def test_format_sparkle_smoke_report_ok():
    report = SparkleSmokeReport(
        ok=True,
        app_bundle="/Applications/Expando.app",
        helper_path="/Applications/Expando.app/Contents/MacOS/expando-sparkle",
        framework_present=True,
        errors=[],
    )
    text = format_sparkle_smoke_report(report)
    assert "Sparkle smoke test" in text
    assert "OK" in text


def test_format_sparkle_smoke_report_fail():
    report = SparkleSmokeReport(
        ok=False,
        app_bundle="/tmp/Expando.app",
        helper_path=None,
        framework_present=False,
        errors=["Sparkle.framework missing"],
    )
    text = format_sparkle_smoke_report(report)
    assert "FAIL" in text
    assert "Sparkle.framework missing" in text