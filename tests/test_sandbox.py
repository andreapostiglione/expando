import pytest

from expando.config import AppConfig, Match, Variable
from expando.renderer import render_match


def test_shell_allowlist_blocks_command():
    match = Match(
        triggers=[":bad"],
        replace="{{output}}",
        vars=[Variable(name="output", type="shell", params={"cmd": "rm -rf /"})],
    )
    app = AppConfig(shell_allowlist=["echo", "git"])
    with pytest.raises(RuntimeError, match="not allowed"):
        render_match(match, app_config=app)


def test_shell_allowlist_allows_command():
    match = Match(
        triggers=[":ok"],
        replace="{{output}}",
        vars=[Variable(name="output", type="shell", params={"cmd": "echo ok"})],
    )
    app = AppConfig(shell_allowlist=["echo"])
    assert render_match(match, app_config=app) == "ok"