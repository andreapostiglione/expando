from pathlib import Path
from unittest.mock import patch

from expando.doctor_repair import launch_agent_needs_refresh, repair_launch_agent


def test_launch_agent_needs_refresh_when_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("expando.doctor_repair.platform.system", lambda: "Darwin")
    source = tmp_path / "source.plist"
    source.write_bytes(
        b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.andreapostiglione.expando</string>
<key>ThrottleInterval</key><integer>15</integer>
<key>ProgramArguments</key><array><string>/tmp/launch-expando.sh</string></array>
</dict></plist>"""
    )
    monkeypatch.setattr("expando.doctor_repair._source_launch_agent_path", lambda: source)
    monkeypatch.setattr(
        "expando.doctor_repair._installed_launch_agent_path",
        lambda: tmp_path / "missing.plist",
    )
    assert launch_agent_needs_refresh() is True


def test_repair_launch_agent_runs_install_script(tmp_path: Path, monkeypatch) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    script = scripts / "install-launch-agent.sh"
    script.write_text("#!/bin/bash\n", encoding="utf-8")
    monkeypatch.setattr("expando.doctor_repair.package_root", lambda: tmp_path)
    monkeypatch.setattr("expando.doctor_repair.platform.system", lambda: "Darwin")
    monkeypatch.setattr("expando.doctor_repair.launch_agent_needs_refresh", lambda: True)
    with patch("expando.doctor_repair.subprocess.run") as run:
        actions = repair_launch_agent()
    assert actions == ["reinstalled_launch_agent"]
    run.assert_called_once()