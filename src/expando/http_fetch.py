"""HTTPS-only URL helpers for remote config / hub / update feeds."""

from __future__ import annotations

from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def require_https_url(url: str) -> str:
    """Return *url* if it is a safe https URL; raise ValueError otherwise."""
    cleaned = (url or "").strip()
    if not cleaned:
        raise ValueError("URL is empty")
    parsed = urlparse(cleaned)
    if parsed.scheme.lower() != "https":
        raise ValueError(f"Only https URLs are allowed (got {parsed.scheme or 'missing'})")
    if not parsed.netloc:
        raise ValueError("URL host is missing")
    # Block credentials in URL and obvious local schemes already excluded by https-only.
    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not allowed")
    return cleaned


def https_get_text(url: str, *, timeout: float = 20) -> str:
    """GET *url* over HTTPS and return decoded body text."""
    safe = require_https_url(url)
    request = Request(safe, headers={"User-Agent": "Expando"})
    try:
        # Scheme restricted to https by require_https_url above.
        with urlopen(request, timeout=timeout) as response:  # nosec B310
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except URLError as exc:
        raise URLError(f"HTTPS fetch failed for {safe}: {exc}") from exc


def https_get_bytes(url: str, *, timeout: float = 20) -> bytes:
    safe = require_https_url(url)
    request = Request(safe, headers={"User-Agent": "Expando"})
    with urlopen(request, timeout=timeout) as response:  # nosec B310
        return response.read()
