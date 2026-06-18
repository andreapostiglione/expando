# Self-hosted E2E (macOS)

Full keyboard listener tests need a Mac with **Accessibility** and **Input Monitoring** granted to the runner process.

Clipboard injection tests additionally require working `pbcopy`/`pbpaste` and Accessibility for Cmd+V paste.

## Enable CI

1. Register a self-hosted runner with labels `self-hosted` and `macos`.
2. Ensure **Python 3.10+** is on `PATH` (Homebrew `python3` is fine). The workflow does not use `actions/setup-python` because v6 hardcodes `/Users/runner` on macOS self-hosted runners.
3. Set the repository variable:

```bash
gh variable set ENABLE_SELF_HOSTED_E2E --body true --repo andreapostiglione/expando
```

4. Grant **Accessibility** and **Input Monitoring** to the runner service (System Settings → Privacy & Security).
5. Run the workflow once interactively on the runner host so clipboard paste works in the runner session.

6. Push to `main` or run workflow **E2E (self-hosted)** manually.

## Run locally

```bash
export EXPANDO_E2E_FULL=1
export EXPANDO_E2E_CLIPBOARD=1
export EXPANDO_E2E_IMAGE=1
pytest -q tests/e2e -ra
```

Injection tests (TextEdit) need Accessibility. The global listener test also needs Input Monitoring.
The clipboard test is marked `@pytest.mark.clipboard` and skips when TCC is incomplete.
Image snippet tests use `@pytest.mark.image` and verify PNG clipboard paste into TextEdit.

## Notarization audit (weekly)

With the same self-hosted runner enabled, workflow **Notarization audit** downloads the latest release DMG and runs:

```bash
expando notarize-audit --app Expando.app --dmg Expando.dmg --strict
```

Release builds also run the audit immediately after DMG creation when notarization secrets are configured.