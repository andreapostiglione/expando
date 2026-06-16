from __future__ import annotations

import re
from html.parser import HTMLParser


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def text(self) -> str:
        return "".join(self._parts)


def html_to_plain(text: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(text)
    parser.close()
    return re.sub(r"\n{3,}", "\n\n", parser.text()).strip()


def markdown_to_plain(text: str) -> str:
    plain = text
    plain = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", plain)
    plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", plain)
    plain = re.sub(r"`([^`]+)`", r"\1", plain)
    plain = re.sub(r"\*\*([^*]+)\*\*", r"\1", plain)
    plain = re.sub(r"\*([^*]+)\*", r"\1", plain)
    plain = re.sub(r"^#{1,6}\s+", "", plain, flags=re.MULTILINE)
    plain = re.sub(r"^>\s?", "", plain, flags=re.MULTILINE)
    return plain.strip()