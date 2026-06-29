# Troubleshooting playbook

Quick fixes for common Expando issues on macOS.

## Expansion does nothing

1. **Check daemon status**
   ```bash
   expando status
   expando doctor
   ```
2. **Grant permissions** — System Settings → Privacy & Security:
   - **Accessibility** for `Expando.app`
   - **Input Monitoring** for `Expando.app`
3. **Run setup wizard**
   ```bash
   expando setup
   ```
4. **Verify snippets load**
   ```bash
   expando match :yourtrigger
   ```

Current DMG/Homebrew builds should appear as `Expando.app` in Privacy & Security.
If macOS shows `python3.12`, update or reinstall Expando before re-granting permissions.

## Expando stops after password field

Secure Input blocks expansion while a secure text field is focused. This is expected when
`respect_secure_input: true` (default). Check runtime health:

```bash
expando health --json
```

## Duplicate daemon / stale PID

```bash
expando doctor
expando stop
expando start
```

If `doctor` reports multiple processes, stop all Expando instances and restart once.

## Config changes not applied

Ensure `auto_restart: true` in `config/default.yml`, or restart manually:

```bash
expando restart
```

Watch reload count:

```bash
expando health
```

## Sync / iCloud conflicts

```bash
expando sync status
```

Resolve before destructive sync:

- Commit or stash git changes if `git_dirty` is reported
- Remove iCloud conflict markers (`*.icloud` placeholders)
- Edit snippets from **one Mac at a time**

`expando sync icloud` refuses to run when conflicts are detected.

## Crashes and safe mode

After repeated crashes Expando enters **safe mode** (expansion disabled).

```bash
expando doctor --full-html   # includes crash loop trend
expando crashes
expando health --json
```

Restart after fixing config errors:

```bash
expando restart
```

## Backups

```bash
expando backup
expando doctor    # warns if auto-backup is stale
```

Automatic backups run on daemon start when `auto_backup` is `daily` or `weekly`.
Pre-mutation backups are created before `restore`, `hub install --force`, and `sync icloud`.

## Collecting diagnostics

```bash
expando support-bundle -o ~/Desktop/expando-support.tar.gz
expando logs --json -n 200
expando doctor --doctor-json
expando health --json
```

The support bundle contains redacted config, doctor JSON, recent logs, and crash reports.

## Updates

```bash
expando check-updates
expando sparkle-smoke
```

From the menu bar: **Check for updates** (Sparkle when bundled, otherwise appcast).

## Still stuck?

1. Review [ARCHITECTURE.md](ARCHITECTURE.md) for component boundaries
2. Open an issue with a support bundle (no secrets)
3. For CI/E2E failures see [E2E_RUNNERS.md](E2E_RUNNERS.md)
