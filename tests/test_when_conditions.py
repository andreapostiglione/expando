from __future__ import annotations

from expando.app_context import AppContext
from expando.when_conditions import evaluate_when, when_needs_form


def test_when_hour_range():
    context = AppContext(name="Terminal")
    assert evaluate_when({"hour": "0-24"}, context) is True


def test_when_app_filter():
    context = AppContext(name="TextEdit")
    assert evaluate_when({"app": ["Terminal"]}, context) is False
    assert evaluate_when({"app": ["TextEdit"]}, context) is True


def test_when_env_and_form():
    context = AppContext(name="Terminal")
    assert evaluate_when({"env": {"EXPANDO_TEST": "1"}}, context) is False
    assert when_needs_form({"form": {"role": "admin"}}) is True
    assert (
        evaluate_when(
            {"form": {"role": "admin"}},
            context,
            form_values={"role": "admin"},
            require_form=True,
        )
        is True
    )