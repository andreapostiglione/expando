# Self-hosted E2E (macOS)

Full keyboard listener tests need a Mac with **Accessibility** and **Input Monitoring** granted to the runner process.

## Enable CI

1. Register a self-hosted runner with labels `self-hosted` and `macos`.
2. Set the repository variable:

```bash
gh variable set ENABLE_SELF_HOSTED_E2E --body true --repo andreapostiglione/expando
```

3. Push to `main` or run workflow **E2E (self-hosted)** manually.

## Run locally

```bash
export EXPANDO_E2E_FULL=1
pytest -q tests/e2e -ra
```

Injection tests (TextEdit) need Accessibility. The global listener test also needs Input Monitoring.