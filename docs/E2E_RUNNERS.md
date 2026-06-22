# E2E runners and failover

Expando E2E tests that exercise live macOS injection require a **self-hosted macOS runner**
with Accessibility and Input Monitoring granted to the runner process.

## Workflows

| Workflow | Schedule | Runner | Purpose |
|----------|----------|--------|---------|
| `e2e-self-hosted.yml` | Mon 06:00 UTC + push | `self-hosted, macos` | Primary full E2E on `main` |
| `e2e-nightly.yml` | Daily 05:00 UTC | `self-hosted, macos` | Redundant nightly regression |

Both workflows are gated by repository variable `ENABLE_SELF_HOSTED_E2E=true`.

## Primary runner

1. Register a self-hosted runner with labels `self-hosted` and `macos`.
2. Install Python 3.10+ (Homebrew `python3` is fine).
3. Grant **Accessibility** and **Input Monitoring** to the runner service account.
4. Set `ENABLE_SELF_HOSTED_E2E=true` on the repository.

See [E2E_SELF_HOSTED.md](E2E_SELF_HOSTED.md) for local reproduction and clipboard checks.

## Redundant / failover runner

`e2e-nightly.yml` provides a second daily run on the same runner label. If the primary job
fails or the variable is unset, a lightweight **failover** job documents the outage instead of
silently skipping.

For true hardware redundancy:

1. Register a **second** macOS machine with the same labels (`self-hosted`, `macos`).
2. GitHub Actions distributes jobs across available runners with matching labels.
3. Keep TCC permissions aligned on both hosts.

If both runners are offline, nightly artifacts are not produced; check the failover job log and
re-enable `ENABLE_SELF_HOSTED_E2E`.

## Environment flags

| Variable | Meaning |
|----------|---------|
| `EXPANDO_E2E_FULL=1` | Enable full listener / secure-input E2E |
| `EXPANDO_E2E_CLIPBOARD=1` | Enable clipboard injection E2E |
| `EXPANDO_E2E_IMAGE=1` | Enable image clipboard E2E |

Tests marked `@pytest.mark.integration` skip on headless GitHub-hosted runners unless
`EXPANDO_E2E_FULL=1` is set on a self-hosted host.

## Soak smoke (optional)

For long-running daemon stability on a self-hosted runner, use:

```bash
chmod +x scripts/soak-health-check.sh
./scripts/soak-health-check.sh 24 300
```

This runs `expando health` and a short `expando doctor` summary every 5 minutes for 2 hours.
Pair it with `e2e-nightly.yml` on a second physical Mac for hardware redundancy.