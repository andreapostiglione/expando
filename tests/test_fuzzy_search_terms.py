from expando.fuzzy import fuzzy_filter_search_items, item_search_text


def test_item_search_text_includes_search_terms():
    text = item_search_text(
        {
            "label": "Email",
            "trigger": ":mail",
            "search_terms": ["posta", "indirizzo"],
        }
    )
    assert "posta" in text
    assert "indirizzo" in text


def test_fuzzy_filter_search_items_matches_search_terms():
    items = [
        {"id": "0", "trigger": ":x", "label": "Other", "search_terms": []},
        {"id": "1", "trigger": ":mail", "label": "Email", "search_terms": ["posta"]},
    ]
    filtered = fuzzy_filter_search_items("posta", items)
    assert len(filtered) == 1
    assert filtered[0]["trigger"] == ":mail"