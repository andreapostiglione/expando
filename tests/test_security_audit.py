from pathlib import Path

import yaml

from expando.security_audit import run_security_audit


def test_security_audit_passes_clean_config(tmp_path: Path):
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text(
        "shell_allowlist:\n  - echo\n",
        encoding="utf-8",
    )
    (config_dir / "match" / "base.yml").write_text(
        "matches:\n  - trigger: ':hi'\n    replace: 'Hello'\n",
        encoding="utf-8",
    )

    report = run_security_audit(config_dir)
    assert report.ok
    check_ids = {item.check_id for item in report.findings}
    assert "hub.index" in check_ids
    assert "plugins.path_traversal" in check_ids


def test_security_audit_fails_shell_without_allowlist(tmp_path: Path):
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text("shell_allowlist: []\n", encoding="utf-8")
    match = {
        "matches": [
            {
                "trigger": ":x",
                "replace": "{{out}}",
                "vars": [{"name": "out", "type": "shell", "params": {"cmd": "echo hi"}}],
            }
        ]
    }
    (config_dir / "match" / "base.yml").write_text(
        yaml.safe_dump(match, allow_unicode=True),
        encoding="utf-8",
    )

    report = run_security_audit(config_dir)
    assert not report.ok
    assert any(item.check_id == "shell.allowlist" and item.status == "fail" for item in report.findings)


def test_security_audit_flags_shell_newline_chaining(tmp_path: Path):
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text(
        "shell_allowlist:\n  - echo\n",
        encoding="utf-8",
    )
    match = {
        "matches": [
            {
                "trigger": ":x",
                "replace": "{{out}}",
                "vars": [
                    {
                        "name": "out",
                        "type": "shell",
                        "params": {"cmd": "echo hi\nprintf BYPASS"},
                    }
                ],
            }
        ]
    }
    (config_dir / "match" / "base.yml").write_text(
        yaml.safe_dump(match, allow_unicode=True),
        encoding="utf-8",
    )

    report = run_security_audit(config_dir)

    assert not report.ok
    assert any(item.check_id == "shell.chaining" and item.status == "fail" for item in report.findings)
