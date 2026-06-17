from expando.runtime_info import detect_runtime


def test_detect_runtime_returns_info():
    runtime = detect_runtime()
    assert runtime.mode in {"app", "dev", "venv", "unknown"}
    assert runtime.grant_label
    assert runtime.executable