from expando.i18n import t, tf


def test_default_locale_is_italian():
    assert "attivo" in tf("cli.status.running", pid=42)


def test_english_locale_override():
    assert "running" in tf("cli.status.running", pid=42, locale="en")


def test_template_header_italian():
    assert "Template" in t("cli.templates.header")