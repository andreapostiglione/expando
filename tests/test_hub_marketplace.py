from pathlib import Path

from expando.hub_marketplace import create_submission_bundle, format_submission_instructions
from expando.paths import package_root


def test_create_submission_bundle(tmp_path: Path):
    source = package_root() / "default_config" / "match" / "packages" / "social"
    submission = create_submission_bundle(source)
    assert submission.package_id == "social"
    assert submission.bundle_path.exists()
    text = format_submission_instructions(submission, bundle_path=tmp_path / "out.zip")
    assert "social" in text
    assert "github.com" in text