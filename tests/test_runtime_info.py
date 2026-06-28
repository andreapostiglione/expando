import sys

from expando.runtime_info import detect_runtime


def test_detect_runtime_returns_info():
    runtime = detect_runtime()
    assert runtime.mode in {"app", "packaged", "dev", "venv", "unknown"}
    assert runtime.grant_label
    assert runtime.executable


def test_detect_runtime_recognizes_packaged_python(monkeypatch, tmp_path):
    resources = tmp_path / "Expando.app" / "Contents" / "Resources"
    resources.mkdir(parents=True)
    executable = tmp_path / "python3.12"
    executable.touch()

    monkeypatch.setenv("EXPANDO_RESOURCES", str(resources))
    monkeypatch.setattr(sys, "executable", str(executable))

    runtime = detect_runtime()

    assert runtime.mode == "packaged"
    assert runtime.grant_label == "python3.12"
    assert runtime.grant_hint.endswith("Expando.app")
