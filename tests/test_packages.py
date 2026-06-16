from pathlib import Path

from expando.packages import list_installed_packages, load_package_matches


def test_load_package_matches(tmp_path: Path):
    package_dir = tmp_path / "packages" / "core"
    package_dir.mkdir(parents=True)
    (package_dir / "snippets.yml").write_text(
        "matches:\n  - trigger: ':pkg'\n    replace: 'from package'\n",
        encoding="utf-8",
    )
    matches = load_package_matches(tmp_path)
    assert len(matches) == 1
    assert matches[0].triggers == [":pkg"]


def test_list_installed_packages(tmp_path: Path):
    package_dir = tmp_path / "packages" / "core"
    package_dir.mkdir(parents=True)
    (package_dir / "snippets.yml").write_text("matches: []\n", encoding="utf-8")
    assert list_installed_packages(tmp_path) == ["core"]