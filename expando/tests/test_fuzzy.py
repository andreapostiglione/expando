from expando.fuzzy import fuzzy_score


def test_fuzzy_score_substring_prefers_prefix():
    assert fuzzy_score("cl", ":claude") > fuzzy_score("cl", ":shell")


def test_fuzzy_score_subsequence():
    assert fuzzy_score("cde", ":claude") > 0