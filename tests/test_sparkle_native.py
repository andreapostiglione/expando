from expando.sparkle_native import sparkle_available, sparkle_framework_path
from expando.paths import package_root


def test_sparkle_framework_path_when_missing():
    bundle = package_root() / "Expando.app"
    assert sparkle_framework_path(bundle) is None


def test_sparkle_available_false_without_helper():
    assert sparkle_available() is False