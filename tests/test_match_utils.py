from expando.config import Match
from expando.match_utils import extract_triggers, find_duplicate_literal_triggers


def test_extract_triggers_single():
    assert extract_triggers({"trigger": ":a"}) == [":a"]


def test_extract_triggers_multiple():
    assert extract_triggers({"triggers": [":a", ":b"]}) == [":a", ":b"]


def test_find_duplicate_literal_triggers():
    matches = [
        Match(triggers=[":dup"], replace="one"),
        Match(triggers=[":dup"], replace="two"),
        Match(triggers=[r"\d+"], replace="num", regex=True),
    ]
    assert find_duplicate_literal_triggers(matches) == [":dup"]