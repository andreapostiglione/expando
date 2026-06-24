from pathlib import Path
from unittest.mock import patch

from expando.app_context import AppContext
from expando.config import AppConfig, ConfigBundle, Match
from expando.engine import ExpansionEngine
from expando.injector import InjectorSettings, TextInjector


def test_engine_image_expansion_falls_back_to_replace(tmp_path: Path):
    config_dir = tmp_path / "expando"
    images = config_dir / "images"
    images.mkdir(parents=True)
    (images / "logo.png").write_bytes(b"\x89PNG\r\n")

    match = Match(
        triggers=[":logo"],
        replace="fallback text",
        image="images/logo.png",
    )
    config = ConfigBundle(app=AppConfig(respect_secure_input=False), matches=[match])
    injector = TextInjector(InjectorSettings())
    engine = ExpansionEngine(config=config, injector=injector, config_dir=config_dir)

    injected: list[str] = []
    engine.injector.inject = lambda text, **kwargs: injected.append(text)  # type: ignore[method-assign]
    engine.injector.delete_chars = lambda count: None  # type: ignore[method-assign]
    engine.injector.inject_image = lambda path: False  # type: ignore[method-assign]

    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="Terminal"),
    ), patch("expando.engine.render_match_interactive", return_value="fallback text"):
        for char in ":logo":
            engine.handle_char(char)

    assert injected == ["fallback text"]