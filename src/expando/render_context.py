from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RenderContext:
    config_dir: str | None = None
    trigger: str = ""
    app_name: str = ""
    bundle_id: str = ""
    window_title: str = ""
    form_values: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "trigger": self.trigger,
            "app_name": self.app_name,
            "bundle_id": self.bundle_id,
            "window_title": self.window_title,
            "form": dict(self.form_values),
            "config_dir": self.config_dir or "",
        }