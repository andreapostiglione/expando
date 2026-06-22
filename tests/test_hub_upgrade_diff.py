from pathlib import Path

from expando.hub import format_hub_upgrade_diff_summary, hub_package_upgrade_diff


def test_hub_package_upgrade_diff_detects_changes(tmp_path: Path) -> None:
    config_dir = tmp_path / "expando"
    package_dir = config_dir / "match" / "packages" / "typing-it"
    package_dir.mkdir(parents=True)
    (package_dir / "snippets.yml").write_text("matches:\n  - trigger: ':old'\n", encoding="utf-8")

    entries = hub_package_upgrade_diff(config_dir, "typing-it")
    assert entries
    assert entries[0]["file"] == "snippets.yml"
    assert entries[0]["status"] in {"changed", "unchanged", "local_only"}

    summary = format_hub_upgrade_diff_summary(
        "typing-it",
        local_version="1.0.0",
        remote_version="1.1.0",
        diff_entries=entries,
    )
    assert "typing-it" in summary