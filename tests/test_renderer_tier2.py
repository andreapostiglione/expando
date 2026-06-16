from expando.config import Match, Variable
from expando.renderer import render_match


def test_render_random_variable():
    match = Match(
        triggers=[":pick"],
        replace="{{choice}}",
        vars=[
            Variable(
                name="choice",
                type="random",
                params={"choices": ["a", "b", "c"]},
            )
        ],
    )
    rendered = render_match(match)
    assert rendered in {"a", "b", "c"}


def test_render_unicode_variable_and_replace():
    match = Match(
        triggers=[":uni"],
        replace=r"{{symbol}} and \u0042",
        vars=[
            Variable(
                name="symbol",
                type="unicode",
                params={"value": r"\u2764"},
            )
        ],
    )
    rendered = render_match(match)
    assert rendered == "❤ and B"