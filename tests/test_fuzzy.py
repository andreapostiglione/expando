from expando.fuzzy import fuzzy_filter, fuzzy_score


def test_fuzzy_score_substring_prefers_prefix():
    assert fuzzy_score("cl", ":claude") > fuzzy_score("cl", ":shell")


def test_fuzzy_score_subsequence():
    assert fuzzy_score("cde", ":claude") > 0


def test_fuzzy_filter_orders_best_matches_first():
    items = [":shell", ":claude", ":date"]
    assert fuzzy_filter("cl", items)[0] == ":claude"


def test_fuzzy_filter_empty_query_returns_all():
    items = [":a", ":b"]
    assert fuzzy_filter("", items) == items