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


def test_render_builtin_env_token():
    match = Match(triggers=[":user"], replace="{{USER}}")
    rendered = render_match(match)
    assert rendered