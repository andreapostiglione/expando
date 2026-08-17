from __future__ import annotations

import pytest

from expando.http_fetch import require_https_url


def test_require_https_url_accepts_https():
    assert require_https_url("https://example.com/appcast.xml").startswith("https://")


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/x",
        "file:///etc/passwd",
        "ftp://example.com/x",
        "https://user:pass@example.com/x",
        "",
        "not-a-url",
    ],
)
def test_require_https_url_rejects_unsafe(url: str):
    with pytest.raises(ValueError):
        require_https_url(url)
