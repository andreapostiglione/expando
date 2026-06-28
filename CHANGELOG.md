# Changelog

All notable changes to Expando are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [3.29.12] — 2026-06-28

### Fixed
- Distribution launcher disables Python bytecode writes so first launch no longer creates or modifies `__pycache__` inside the signed app bundle.
- Distribution builds install dependencies with `--no-compile`, remove bundled `__pycache__`, and run verification with `PYTHONDONTWRITEBYTECODE=1` to keep the signed bundle sealed.

## [3.29.11] — 2026-06-28

### Fixed
- Sparkle helper now links with `@executable_path/../Frameworks` RPATH so it can load the bundled `Sparkle.framework` at runtime.
- Distribution verification now fails if the Sparkle helper references `@rpath/Sparkle.framework` without a bundle-local framework RPATH.

## [3.29.10] — 2026-06-28

### Fixed
- Distribution launcher now requires Python 3.12 explicitly, matching the bundled CPython 3.12 native PyObjC wheels instead of accidentally using Homebrew's generic `python3`.
- Release bundle verification now imports PyObjC and `pynput.keyboard` with Python 3.12, so ABI mismatches fail before a DMG is shipped.
- Homebrew cask generators declare `depends_on formula: "python@3.12"` for a working runtime on fresh installs.

## [3.29.9] — 2026-06-28

### Fixed
- Bundled LaunchAgent startup now resolves `Expando.app/Contents/MacOS/expando` from inside `Contents/Resources`, so onboarding/doctor repair no longer falls back to creating a source-style `.venv` inside the installed app.
- Distribution verification now fails if the bundled launch script cannot resolve the app executable.

## [3.29.8] — 2026-06-28

### Fixed
- Native snippet editor layout now uses a compact two-column advanced section and no longer overlaps labels, inputs, and text areas.
- AppKit text updates preserve text view editability, so loading a snippet no longer turns editor fields into read-only views.
- Snippet list selection now uses the correct AppKit table delegate callback and updates the detail panel reliably.

## [3.29.7] — 2026-06-28

### Added
- Menu bar now exposes a direct **New snippet** action that opens the graphical editor already in create mode.

### Fixed
- New-snippet mode clears advanced editor fields before saving, avoiding stale app/bundle/title filters from the previously selected snippet.
- Closing the snippet editor without saving no longer reports a false UI failure from the menu bar.

## [3.29.6] — 2026-06-27

### Fixed
- Release DMGs are now signed as containers before notarization, so Gatekeeper primary-signature assessment accepts the downloaded `Expando.dmg` as well as the app bundle inside it.
- Notarization audit now fails if the DMG container is unsigned or rejected by `spctl --type open --context context:primary-signature`.

## [3.29.5] — 2026-06-27

### Security
- Shell variables now execute allowlisted commands with `shell=False` and reject shell chaining/control characters, including newline command injection.
- Plugin script and image path resolution now use canonical `Path.relative_to()` containment checks to block prefix-sibling traversal such as `../expando_evil.png`.

### Fixed
- Expansion with `word_break` or postponed suffix now deletes the full typed trigger plus suffix before reinserting replacement text.
- Cursor hint injection no longer deadlocks when `inject(..., cursor_left=...)` calls cursor movement internally.
- Official `sales-it` package trigger renamed from `:followup` to `:salesfollowup` to avoid cross-package conflicts.

### Changed
- Distribution bundles now copy and verify `default_config`, hub metadata, and runtime launch scripts.
- Live TextEdit/macOS E2E tests are opt-in via `EXPANDO_E2E_TEXTEDIT=1`, `EXPANDO_E2E_CLIPBOARD=1`, `EXPANDO_E2E_IMAGE=1`, or `EXPANDO_E2E_FULL=1`.
- Sparkle release builds now require a public EdDSA key in the app bundle, and appcast generation requires `SPARKLE_PRIVATE_KEY` unless explicitly generating a local unsigned appcast.
- Added open-source contribution, security, code of conduct, and Dependabot metadata.

## [3.29.4] — 2026-06-27

### Fixed
- Clipboard permission probe no longer pollutes the user's pasteboard outside `expando doctor`.
- Release health docs and Sparkle benchmark history were refreshed for v3.29.4.

## [3.29.3] — 2026-06-27

### Fixed
- Clipboard readiness checks avoid destructive pasteboard probes during normal runtime.

## [3.29.2] — 2026-06-27

### Fixed
- Release appcast and health artifacts refreshed after clipboard and distribution fixes.

## [3.29.1] — 2026-06-22

### Fixed
- **DMG non si avviava** — il venv nel bundle puntava a path CI (`/Users/runner/...`) e a Python.framework assente sul Mac utente
- Build distribuzione: `site-packages` nel bundle + Python 3.10+ di sistema (niente venv CI)
- Doppio click su `Expando.app` ora esegue `expando run` (icona menu bar) invece di uscire subito
- Script `scripts/repair-installed-app.sh` per riparare installazioni DMG già rotte

## [3.29.0] — 2026-06-21

### Added
- Menu bar: **Stato runtime** (`expando health` in un click)
- Menu bar: **Pausa temporanea** (1h / 4h / riprendi) con badge ⏸
- Menu bar: badge **🔒** quando Accessibilità o Monitoraggio input mancano
- Menu bar: **Aggiorna pacchetti hub** con anteprima diff YAML prima dell'upgrade
- Wizard permessi: badge live su Accessibilità + Monitoraggio input; recheck sul passo input
- `doctor --repair` reinstalla LaunchAgent se il plist installato è obsoleto
- `snooze.json` — pausa espansione temporanea senza disattivare il daemon
- Script `scripts/soak-health-check.sh` per smoke ripetuto su runner self-hosted

### Changed
- Editor snippet: placeholder ricerca localizzato (`editor.search_placeholder`)
- Priorità badge menu bar: listener ⚠ → permessi 🔒 → snooze ⏸ → hub ↑N → disabilitato ○

## [3.28.0] — 2026-06-21

### Added
- `atomic_io.py` — scritture JSON atomiche per crash-loop, health e injection-health
- `ui_main_thread.py` — dispatch sicuro UI AppKit dal main thread
- `menubar_feedback.py` — dialog nativi per backup, restore, errori menu bar
- `ui_file_picker.py` — picker file per editor snippet (duplica/sposta)
- `wait_for_stable_config()` — attende YAML stabili prima del reload
- Notifiche macOS all'avvio se Accessibilità o Monitoraggio input mancanti
- `expando doctor --repair` cancella anche safe mode
- `scripts/push-homebrew-tap-pr.sh` + step CI per PR automatica su homebrew-tap
- LaunchAgent: `ThrottleInterval` 15s per evitare respawn troppo rapidi
- Test: watchdog retry, start_daemon timeout, config stability, safe-mode repair (+355 test totali)

### Fixed
- **Listener watchdog** — retry periodico (30s) invece di arrendersi al primo fallimento
- **Deadlock engine** — lock rilasciato prima di render/inject/undo (form UI + menu bar)
- **Riavvio menu bar** — nuova istanza parte solo dopo exit del vecchio PID (niente doppio listener)
- **Crash reporting** — ogni crash report alimenta `crash-loop.json` per safe mode/backoff
- **start_daemon** — fallisce se il pid file non compare (niente pid parent fasullo)
- **Config reload** — last-good salvato prima di `engine.reload`; rollback più affidabile
- **Menu bar threading** — `_sync_enabled_label` non tocca rumps da background thread
- **Injecting timers** — cancellati su `service.stop()` (niente gate espansione bloccato)
- **Menubar path** — `service.stop()` in `finally` su uscita
- **Restore backup** — picker multi-backup, esclusi snapshot pre-restore
- **Restart foreground** — niente `os.execve` con NSApplication attiva

### Changed
- `ui_state` timeout 320s (allineato a UI subprocess 300s)
- `call_on_main_thread` — errore esplicito se PyObjC manca con `wait=True`

## [3.27.0] — 2026-06-19

### Added
- Editor: duplica/sposta snippet tra file YAML con picker
- Release CI: PR automatica su `homebrew-tap`
- Menu bar: dialog nativi backup/restore/restart, reveal in Finder

## [3.26.0] — 2026-06-18

### Added
- Auto-backup schedulato, sync conflict detection, backup pre-mutation
- Plugin allowlist, crash trend HTML, docs (YAML / Troubleshooting / Architecture)
- E2E nightly workflow + runner failover documentation

[3.29.12]: https://github.com/andreapostiglione/expando/compare/v3.29.11...v3.29.12
[3.29.11]: https://github.com/andreapostiglione/expando/compare/v3.29.10...v3.29.11
[3.29.10]: https://github.com/andreapostiglione/expando/compare/v3.29.9...v3.29.10
[3.29.9]: https://github.com/andreapostiglione/expando/compare/v3.29.8...v3.29.9
[3.29.8]: https://github.com/andreapostiglione/expando/compare/v3.29.7...v3.29.8
[3.29.7]: https://github.com/andreapostiglione/expando/compare/v3.29.6...v3.29.7
[3.29.6]: https://github.com/andreapostiglione/expando/compare/v3.29.5...v3.29.6
[3.29.5]: https://github.com/andreapostiglione/expando/compare/v3.29.4...v3.29.5
[3.29.4]: https://github.com/andreapostiglione/expando/compare/v3.29.3...v3.29.4
[3.29.3]: https://github.com/andreapostiglione/expando/compare/v3.29.2...v3.29.3
[3.29.2]: https://github.com/andreapostiglione/expando/compare/v3.29.1...v3.29.2
[3.29.1]: https://github.com/andreapostiglione/expando/compare/v3.29.0...v3.29.1
[3.29.0]: https://github.com/andreapostiglione/expando/compare/v3.28.0...v3.29.0
[3.28.0]: https://github.com/andreapostiglione/expando/compare/v3.27.0...v3.28.0
[3.27.0]: https://github.com/andreapostiglione/expando/compare/v3.26.0...v3.27.0
[3.26.0]: https://github.com/andreapostiglione/expando/releases/tag/v3.26.0
