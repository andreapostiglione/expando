from __future__ import annotations

import json
import sys

from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(2)

    command = sys.argv[1]
    payload = json.loads(sys.stdin.read() or "{}")

    if command == "search":
        from .ui_native import run_search_picker

        result = run_search_picker(payload.get("items", []))
    elif command == "form":
        from .ui_native import run_form_dialog

        result = run_form_dialog(payload.get("fields", []))
    elif command == "editor":
        from .snippet_editor import open_snippet_editor

        config_dir = payload.get("config_dir")
        if not config_dir:
            raise SystemExit(2)
        result = open_snippet_editor(Path(config_dir))
    else:
        raise SystemExit(2)

    print(json.dumps(result or {}))


if __name__ == "__main__":
    main()