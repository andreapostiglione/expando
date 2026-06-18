from unittest.mock import patch

from expando.benchmark import (
    format_sparkle_benchmark_report,
    run_sparkle_update_benchmark,
)
from expando.updater import UpdateInfo


def test_run_sparkle_update_benchmark_parses_appcast():
    updates = [
        UpdateInfo(version="9.9.9", download_url="https://example.com/Expando.dmg"),
        UpdateInfo(version="3.0.0", download_url="https://example.com/old.dmg"),
    ]

    with patch("expando.sparkle_native.sparkle_available", return_value=False), patch(
        "expando.sparkle_native.resolve_distribution_app_bundle",
        return_value=None,
    ), patch("expando.updater.fetch_appcast", return_value="<rss></rss>"), patch(
        "expando.updater.parse_appcast",
        return_value=updates,
    ):
        result = run_sparkle_update_benchmark()

    assert result.appcast_entries == 2
    assert result.latest_version == "9.9.9"
    assert result.update_available is True
    text = format_sparkle_benchmark_report(result)
    assert "Sparkle" in text or "appcast" in text