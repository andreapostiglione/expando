from expando.sparkle_native import (
    sparkle_available,
    sparkle_framework_path,
    sparkle_public_ed_key_present,
)
from expando.paths import package_root


def test_sparkle_framework_path_when_missing():
    bundle = package_root() / "Expando.app"
    assert sparkle_framework_path(bundle) is None


def test_sparkle_available_false_without_helper(monkeypatch, tmp_path):
    monkeypatch.setenv("EXPANDO_APP_BUNDLE", str(tmp_path / "Missing.app"))
    assert sparkle_available() is False


def test_sparkle_public_ed_key_present(tmp_path):
    bundle = tmp_path / "Expando.app"
    contents = bundle / "Contents"
    contents.mkdir(parents=True)
    (contents / "Info.plist").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>SUPublicEDKey</key>
  <string>abc123</string>
</dict>
</plist>
""",
        encoding="utf-8",
    )

    assert sparkle_public_ed_key_present(bundle) is True
