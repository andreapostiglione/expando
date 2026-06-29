from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeInfo:
    mode: str
    executable: str
    grant_label: str
    grant_hint: str


def detect_runtime() -> RuntimeInfo:
    executable = Path(sys.executable).resolve()
    exe_str = str(executable)
    resources = os.environ.get("EXPANDO_RESOURCES")

    if resources:
        resources_path = Path(resources).expanduser().resolve()
        if resources_path.name == "Resources" and resources_path.parent.name == "Contents":
            app_root = resources_path.parent.parent
            if app_root.suffix == ".app":
                try:
                    executable.relative_to(app_root)
                    return RuntimeInfo(
                        mode="app",
                        executable=exe_str,
                        grant_label="Expando.app",
                        grant_hint=str(app_root),
                    )
                except ValueError:
                    pass
                return RuntimeInfo(
                    mode="packaged",
                    executable=exe_str,
                    grant_label=executable.name,
                    grant_hint=str(app_root),
                )

    if "Expando.app" in exe_str:
        app_root = executable
        while app_root.name != "Expando.app" and app_root.parent != app_root:
            app_root = app_root.parent
        return RuntimeInfo(
            mode="app",
            executable=exe_str,
            grant_label="Expando.app",
            grant_hint=str(app_root),
        )

    if "Cellar/python" in exe_str or executable.name.lower().startswith("python"):
        return RuntimeInfo(
            mode="dev",
            executable=exe_str,
            grant_label=executable.name,
            grant_hint=exe_str,
        )

    if ".venv" in exe_str:
        return RuntimeInfo(
            mode="venv",
            executable=exe_str,
            grant_label=executable.name,
            grant_hint=exe_str,
        )

    return RuntimeInfo(
        mode="unknown",
        executable=exe_str,
        grant_label=executable.name,
        grant_hint=exe_str,
    )
