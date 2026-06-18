from expando.benchmark import sparkle_helper_strict_fail_enabled


def test_sparkle_helper_strict_fail_enabled(monkeypatch):
    monkeypatch.delenv("EXPANDO_SPARKLE_HELPER_STRICT", raising=False)
    assert sparkle_helper_strict_fail_enabled() is False

    monkeypatch.setenv("EXPANDO_SPARKLE_HELPER_STRICT", "1")
    assert sparkle_helper_strict_fail_enabled() is True

    monkeypatch.setenv("EXPANDO_SPARKLE_HELPER_STRICT", "true")
    assert sparkle_helper_strict_fail_enabled() is True