from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SnippetTemplate:
    id: str
    name: str
    description: str
    match: dict[str, Any]


_BUILTIN_TEMPLATES: dict[str, SnippetTemplate] = {
    "email": SnippetTemplate(
        id="email",
        name="Email reply",
        description="Short professional email with greeting and sign-off",
        match={
            "trigger": "{trigger}",
            "label": "Email reply",
            "replace": (
                "Ciao,\n\n"
                "Grazie per il messaggio.\n\n"
                "Cordiali saluti,\n"
                "{{USER}}"
            ),
        },
    ),
    "signature": SnippetTemplate(
        id="signature",
        name="Email signature",
        description="Multi-line signature block",
        match={
            "trigger": "{trigger}",
            "label": "Signature",
            "replace": (
                "Cordiali saluti,\n"
                "{{USER}}\n"
                "---"
            ),
        },
    ),
    "legal-it": SnippetTemplate(
        id="legal-it",
        name="Legal IT boilerplate",
        description="Standard Italian legal closing paragraph",
        match={
            "trigger": "{trigger}",
            "label": "Legal closing (IT)",
            "replace": (
                "Ai sensi degli artt. 1341 e 1342 c.c., il sottoscritto dichiara "
                "di aver letto e di approvare specificamente le clausole indicate.\n\n"
                "Luogo e data: __________\n"
                "Firma: __________"
            ),
        },
    ),
    "dev": SnippetTemplate(
        id="dev",
        name="Git commit scaffold",
        description="Conventional commit message skeleton",
        match={
            "trigger": "{trigger}",
            "label": "Git commit",
            "replace": "feat(scope): short description\n\n- detail",
        },
    ),
    "logo": SnippetTemplate(
        id="logo",
        name="Image snippet",
        description="Paste a PNG/JPEG from config/images/ (fallback: path text)",
        match={
            "trigger": "{trigger}",
            "label": "Logo image",
            "image": "images/logo.png",
            "replace": "images/logo.png",
            "force_clipboard": True,
        },
    ),
    "meeting": SnippetTemplate(
        id="meeting",
        name="Meeting notes",
        description="Structured meeting notes with attendees and action items",
        match={
            "trigger": "{trigger}",
            "label": "Meeting notes",
            "form": [
                {"name": "title", "label": "Meeting title", "default": "Sync"},
                {"name": "date", "label": "Date", "default": "{{date}}"},
            ],
            "vars": [
                {"name": "date", "type": "date", "params": {"format": "%Y-%m-%d"}},
            ],
            "replace": (
                "# {{title}} — {{date}}\n\n"
                "Attendees:\n- \n\n"
                "Notes:\n- \n\n"
                "Action items:\n- [ ] "
            ),
        },
    ),
}


def list_templates() -> list[SnippetTemplate]:
    return sorted(_BUILTIN_TEMPLATES.values(), key=lambda item: item.id)


def get_template(template_id: str) -> SnippetTemplate:
    key = template_id.strip().lower()
    if key not in _BUILTIN_TEMPLATES:
        known = ", ".join(sorted(_BUILTIN_TEMPLATES))
        raise ValueError(f"Unknown template {template_id!r}. Available: {known}")
    return _BUILTIN_TEMPLATES[key]


def build_match_from_template(template_id: str, trigger: str) -> dict[str, Any]:
    if not trigger.strip():
        raise ValueError("Trigger must not be empty")
    template = get_template(template_id)
    entry = deepcopy(template.match)
    entry["trigger"] = trigger
    if entry.get("label") == template.name:
        entry["label"] = f"{template.name} ({trigger})"
    return entry