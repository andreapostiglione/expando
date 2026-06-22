# Changelog

All notable changes to Expando are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/).

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

[3.29.1]: https://github.com/andreapostiglione/expando/compare/v3.29.0...v3.29.1
[3.29.0]: https://github.com/andreapostiglione/expando/compare/v3.28.0...v3.29.0
[3.28.0]: https://github.com/andreapostiglione/expando/compare/v3.27.0...v3.28.0
[3.27.0]: https://github.com/andreapostiglione/expando/compare/v3.26.0...v3.27.0
[3.26.0]: https://github.com/andreapostiglione/expando/releases/tag/v3.26.0