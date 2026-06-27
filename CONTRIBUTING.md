# Contributing

Thanks for improving Expando. Keep changes focused, tested, and easy to review.

## Development setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest -q tests --ignore=tests/e2e
```

Do not run live macOS E2E tests by default. They can open TextEdit and type into the active
session. Use the explicit flags documented in `docs/E2E_SELF_HOSTED.md` only on a dedicated
runner or local session prepared for those tests.

## Pull requests

- Add or update tests for behavior changes.
- Keep security-sensitive code fail-closed.
- Avoid committing local build artifacts, generated credentials, private notes, or machine-specific paths.
- Update `CHANGELOG.md` for user-visible fixes.

## Release checks

Production releases require signed/notarized DMGs and Sparkle EdDSA appcast signatures.
See `docs/RELEASE.md`.
