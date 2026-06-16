from pathlib import Path

from expando.doctor_checks import find_duplicate_triggers, run_doctor, validate_config_files


def test_validate_config_files_ok(tmp_path: Path):
    config_dir = tmp_path / "config"
    match_dir = tmp_path / "match"
    config_dir.mkdir(parents=True)
    match_dir.mkdir(parents=True)
    (config_dir / "default.yml").write_text("toggle_key: ALT\n", encoding="utf-8")
    (match_dir / "base.yml").write_text(
        "matches:\n  - trigger: ':ok'\n    replace: 'yes'\n",
        encoding="utf-8",
    )
    assert validate_config_files(tmp_path) == []


def test_find_duplicate_triggers(tmp_path: Path):
    match_dir = tmp_path / "match"
    match_dir.mkdir(parents=True)
    (match_dir / "base.yml").write_text(
        "matches:\n"
        "  - trigger: ':dup'\n    replace: 'one'\n"
        "  - trigger: ':dup'\n    replace: 'two'\n",
        encoding="utf-8",
    )
    assert find_duplicate_triggers(tmp_path) == [":dup"]


def test_run_doctor_reports_matches(tmp_path: Path):
    config_dir = tmp_path / "config"
    match_dir = tmp_path / "match"
    config_dir.mkdir(parents=True)
    match_dir.mkdir(parents=True)
    (config_dir / "default.yml").write_text("toggle_key: ALT\n", encoding="utf-8")
    (match_dir / "base.yml").write_text(
        "matches:\n  - trigger: ':hello'\n    replace: 'Hello'\n",
        encoding="utf-8",
    )
    report = run_doctor(tmp_path)
    assert report.match_count == 1
    assert report.config_errors == []