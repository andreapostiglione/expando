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

6. Run workflow **E2E (self-hosted)** manually before releases or when validating macOS GUI behavior.

The workflow is not attached to `push` or a timer because it opens TextEdit and injects
keyboard/clipboard events in the runner's active GUI session.

## Run locally

```bash
export EXPANDO_E2E_FULL=1
export EXPANDO_E2E_CLIPBOARD=1
export EXPANDO_E2E_IMAGE=1
export EXPANDO_E2E_TEXTEDIT=1
pytest -q tests/e2e -ra
```

Injection tests (TextEdit) need Accessibility. The global listener test also needs Input Monitoring.
The clipboard test is marked `@pytest.mark.clipboard` and skips when TCC is incomplete.
Image snippet tests use `@pytest.mark.image` and verify PNG clipboard paste into TextEdit.
Live TextEdit injection tests use `@pytest.mark.integration`, are excluded from headless
`macos-latest` CI (`pytest -m "not clipboard and not image and not integration"`), and
skip unless one of the `EXPANDO_E2E_*` live flags above is set.
If the self-hosted GUI session is frontmost but does not accept synthetic typing or paste
events, live TextEdit tests skip with a readiness message; fix the runner session/TCC grants
before treating those skips as release confidence.

## Notarization audit (weekly)

With the same self-hosted runner enabled, workflow **Notarization audit** downloads the latest release DMG and runs:

```bash
expando notarize-audit --app Expando.app --dmg Expando.dmg --strict
```

Release builds also run the audit immediately after DMG creation when notarization secrets are configured.
