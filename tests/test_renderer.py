from types import SimpleNamespace

import pytest

from expando.config import AppConfig, Match, Variable
from expando.renderer import render_match


def test_render_date_variable():
    match = Match(
        triggers=[":date"],
        replace="{{mydate}}",
        vars=[Variable(name="mydate", type="date", params={"format": "%Y"})],
    )
    rendered = render_match(match)
    assert len(rendered) == 4
    assert rendered.isdigit()


def test_render_shell_variable():
    match = Match(
        triggers=[":shell"],
        replace="{{output}}",
        vars=[Variable(name="output", type="shell", params={"cmd": "echo ok"})],
    )
    app = AppConfig(shell_allowlist=["echo"])
    assert render_match(match, app_config=app) == "ok"


def test_render_shell_variable_rejects_newline_chain():
    match = Match(
        triggers=[":shell"],
        replace="{{output}}",
        vars=[
            Variable(
                name="output",
                type="shell",
                params={"cmd": "echo ok\nprintf BYPASS"},
            )
        ],
    )
    app = AppConfig(shell_allowlist=["echo"])

    with pytest.raises(RuntimeError, match="Shell command not allowed"):
        render_match(match, app_config=app)


def test_render_shell_variable_executes_without_shell(monkeypatch: pytest.MonkeyPatch):
    calls: list[tuple[object, dict[str, object]]] = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout="ok\n", stderr="")

    monkeypatch.setattr("expando.renderer.subprocess.run", fake_run)
    match = Match(
        triggers=[":shell"],
        replace="{{output}}",
        vars=[Variable(name="output", type="shell", params={"cmd": "echo ok"})],
    )
    app = AppConfig(shell_allowlist=["echo"])

    assert render_match(match, app_config=app) == "ok"
    assert calls == [
        (
            ["echo", "ok"],
            {
                "capture_output": True,
                "text": True,
                "timeout": 10,
            },
        )
    ]


def test_render_builtin_env_token():
    match = Match(triggers=[":user"], replace="{{USER}}")
    rendered = render_match(match)
    assert rendered
