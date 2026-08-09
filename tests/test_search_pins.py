from pathlib import Path

from expando.config import Match
from expando.search import SearchItem, rank_search_items
from expando.search_pins import is_pinned, load_pins, pin_trigger, unpin_trigger


def test_pin_roundtrip(tmp_path: Path):
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    pin_trigger(config_dir, ":a")
    pin_trigger(config_dir, ":b")
    # Newest pin is inserted at the front.
    assert load_pins(config_dir) == [":b", ":a"]
    assert is_pinned(config_dir, ":a")
    unpin_trigger(config_dir, ":a")
    assert load_pins(config_dir) == [":b"]


def test_rank_pins_first(tmp_path: Path):
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    pin_trigger(config_dir, ":z")
    match = Match(triggers=[":a"], replace="A")
    items = [
        SearchItem(trigger=":a", match=match),
        SearchItem(trigger=":z", match=match),
        SearchItem(trigger=":m", match=match),
    ]
    ranked = rank_search_items(items, config_dir=config_dir)
    assert [item.trigger for item in ranked] == [":z", ":a", ":m"]
