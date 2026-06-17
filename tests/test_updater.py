from __future__ import annotations

from pathlib import Path

from expando.updater import check_for_updates, latest_update, parse_appcast
from expando.version_utils import is_newer, version_tuple

SAMPLE_APPCAST = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle">
  <channel>
    <item>
      <title>Version 1.5.0</title>
      <sparkle:shortVersionString>1.5.0</sparkle:shortVersionString>
      <enclosure url="https://example.com/1.5.0.dmg" length="100" type="application/octet-stream"/>
    </item>
    <item>
      <title>Version 1.6.0</title>
      <sparkle:shortVersionString>1.6.0</sparkle:shortVersionString>
      <enclosure url="https://example.com/1.6.0.dmg" length="200" type="application/octet-stream"/>
    </item>
  </channel>
</rss>
"""


def test_parse_appcast_reads_versions():
    updates = parse_appcast(SAMPLE_APPCAST)
    assert len(updates) == 2
    latest = latest_update(updates)
    assert latest is not None
    assert latest.version == "1.6.0"
    assert latest.download_url.endswith("1.6.0.dmg")


def test_version_compare():
    assert is_newer("1.6.0", "1.5.0")
    assert not is_newer("1.5.0", "1.6.0")
    assert version_tuple("1.10.0") > version_tuple("1.9.0")


def test_check_for_updates_uses_local_xml(monkeypatch, tmp_path: Path):
    config_dir = tmp_path / "expando"
    config_dir.mkdir()

    monkeypatch.setattr("expando.updater.fetch_appcast", lambda _url=None: SAMPLE_APPCAST)

    result = check_for_updates(config_dir, current_version="1.5.0", force=True)
    assert result.available is not None
    assert result.available.version == "1.6.0"

    up_to_date = check_for_updates(config_dir, current_version="1.6.0", force=True)
    assert up_to_date.available is None