"""Example Expando plugin — copy hooks into your own .py files in plugins/."""


def before_expand(context: dict) -> None:
    """Called before a snippet is rendered."""


def after_expand(context: dict) -> None:
    """Called after expansion; context includes replacement."""


def transform_replacement(text: str, context: dict) -> str:
    """Optional post-processing of rendered text."""
    return text


def run(context: dict) -> str:
    """Used by script variables (type: script, params.path: example.py)."""
    app = context.get("app_name") or "unknown"
    return f"[{app}]"