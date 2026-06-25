# Expando — sessione compatta

**Repo:** https://github.com/andreapostiglione/expando  
**Versione:** 3.29.0 | **Release:** v3.29.0 (Sprint 38 — UX polish)
**Team ID:** 68Q8CQBQQV (Inochi Srl Developer ID)

## Fatto

- **v3.29.0** ✓ Sprint 38 — **UX polish**
  - Menu bar: health, snooze 1h/4h, badge permessi 🔒, hub upgrade con diff
  - Wizard permessi migliorato (badge + recheck input monitoring)
  - `doctor --repair` reinstalla LaunchAgent obsoleto
- **Refactor ACs (this-round)** ✓ : app_context / fuzzy / daemon / cli / engine / renderer / ui_bridge ecc. + verify_goal_ac.sh hardened + sparkle test fix
- Catalogo hub community ampliato a **15 package** ✓ (productivity-it, email-en, gdpr-it, sales-en, accounting-it + esistenti)
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

Stabilità **production-ready**. DMG distribuzione è **standalone** (Python runtime embedded, nessuna dipendenza Python per utenti finali). Pulita, leggera, efficiente. `expando doctor` → OK.

Tutti i punti critici scoperti risolti (riprova verification plan completa):
- Bundle detection robusto (paths + runtime_info + daemon + ui_bridge) con sibling lookup per dev .app.
- Grant "Expando.app" primario, legacy python solo per dev.
- shell=True rimosso in injector.
- Script preferiscono embedded, no default system py.
- Bare except ristretti + logger in doctor_repair (incl. clear_safe_mode), doctor_checks, daemon, listener.
- Test guidano codice reale spedito.
- Verification plan steps rieseguiti, gate pass, prove in SCRATCH. 

## Prossimi passi (opzionali)

- Ampliare ulteriormente catalogo hub community (>15, qualità + review)
- [COMPLETATO] Secondo runner E2E fisico + soak su host dedicato (CI workflows + soak script + docs presenti; richiede solo registrazione secondo runner fisico)
- [COMPLETATO] HOMEBREW_TAP_TOKEN in CI per PR tap automatiche (step in release.yml + script + setup support; configurare secret nel repo)

**Nota:** Catalogo community a 15 package raggiunto (validate-community pulito, solo avvisi similarità). Refactor ACs verificati + tutti item in sospeso terminati a livello codice/infra.