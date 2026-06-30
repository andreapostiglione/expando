from pathlib import Path

from expando.match_store import append_match, format_match_list, import_matches


def test_append_and_list_match(tmp_path: Path):
    append_match(tmp_path, ":hello", "Hello there", target_file="dev.yml")
    output = format_match_list(tmp_path)
    assert ":hello" in output
    assert "Hello there" in output
    assert "dev.yml" not in output
    assert "Personal" in output


def test_import_directory(tmp_path: Path):
    source = tmp_path / "source"
    match_dir = source / "match"
    match_dir.mkdir(parents=True)
    (match_dir / "extra.yml").write_text(
        "matches:\n  - trigger: ':imported'\n    replace: 'ok'\n",
        encoding="utf-8",
    )
    imported = import_matches(tmp_path, match_dir)
    assert imported == ["extra.yml"]
    assert (tmp_path / "match" / "extra.yml").exists()
