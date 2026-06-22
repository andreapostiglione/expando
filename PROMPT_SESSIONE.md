# Expando — sessione compatta

**Repo:** https://github.com/andreapostiglione/expando  
**Versione:** 3.29.0 | **Release:** v3.29.0 (Sprint 38 — UX polish)
**Team ID:** 68Q8CQBQQV (Inochi Srl Developer ID)

## Fatto

- **v3.29.0** ✓ Sprint 38 — **UX polish**
  - Menu bar: health, snooze 1h/4h, badge permessi 🔒, hub upgrade con diff
  - Wizard permessi migliorato (badge + recheck input monitoring)
  - `doctor --repair` reinstalla LaunchAgent obsoleto
- **v3.28.0** ✓ Sprint 37 — **Stability hardening**
  - Watchdog listener: retry 30s, niente listener morto permanente
  - Engine: lock fuori da render/inject/undo (fix deadlock form + menu bar)
  - Daemon: restart menu attende exit PID; start fallisce senza pid file
  - Crash loop ↔ crash reports; JSON atomic writes; LaunchAgent ThrottleInterval
  - Config reload: YAML stabili + last-good prima di reload
  - UI thread: `ui_main_thread`, dialog nativi `menubar_feedback`
  - Doctor repair: safe mode + lock stale; notifiche permessi all'avvio
  - **355** test passati
- **v3.27.0** ✓ Sprint 36 — editor duplica/sposta, tap PR CI, menu bar polish
- **v3.26.0** ✓ Sprint 35 — baseline completa (auto-backup, docs, plugin allowlist)
- Storico: **[ROADMAP.md](ROADMAP.md)** · **[CHANGELOG.md](CHANGELOG.md)**

## Stato

Stabilità **production-ready** in dev (venv + `python3.14` con permessi OK).  
`expando doctor` → OK su macchina dev (giugno 2026). Espansioni `:claude` verificate live.

## Prossimi passi (opzionali)

- Secondo runner E2E fisico + soak su host dedicato
- Ampliare catalogo hub community (15+ package)
- HOMEBREW_TAP_TOKEN in CI per PR tap automatiche