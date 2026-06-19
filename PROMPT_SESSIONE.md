# Expando — sessione compatta

**Repo:** https://github.com/andreapostiglione/expando  
**Versione:** 3.26.0 | **Release:** v3.26.0 (baseline completa — Sprint 28–35)  
**Team ID:** 68Q8CQBQQV (Inochi Srl Developer ID)

## Fatto

- **v3.26.0** ✓ Sprint 35 — baseline completa
  - Auto-backup schedulato, sync conflict, backup pre-mutation
  - Plugin allowlist, crash trend HTML, docs (YAML/Troubleshooting/Architecture)
  - E2E nightly workflow + runner failover doc
- **v3.25.0** ✓ Sprint 34
  - `expando health`, `support-bundle`, `logs --json`
  - E2E secure-input, listener watchdog, editor smoke
  - Hub maintainer sync workflow (weekly dry-run)
- **v3.24.0** ✓ Sprint 33
  - `hub outdated` / `hub upgrade`, notifiche hub doctor/menu bar
  - 10 package community approvati
- **v3.23.0** ✓ Sprint 32
  - Sparkle dev/prod parity, Homebrew cask bump artifact CI
  - Formula in-repo deprecata
- **v3.22.0** ✓ Sprint 31
  - Editor preview live, backup/restore menu bar, restart reale
- **v3.21.0** ✓ Sprint 30
  - Editor regole avanzate, wizard DMG, permission deep-link HTML
- **v3.20.0** ✓ Sprint 29
  - Injection probe, Input Monitoring gate, `doctor --repair`
  - Injection degradation, config reload gate
- **v3.19.0** ✓ Sprint 28
  - Listener watchdog, crash-loop guard, secure-input nativo
- **v3.18.0** ✓ Sprint 27 (hub index manifest, release health sync)
- Vedi storico completo in **[ROADMAP.md](ROADMAP.md)** (Sprint 1–35)

## Stato

Roadmap Tier 6–7 **completa** (Sprint 28–35 → v3.26).  
**310** test unitari. E2E secure-input su runner self-hosted (`EXPANDO_E2E_FULL=1`).

## Prossimi passi (opzionali)

- PR automatica su `homebrew-tap` da release CI
- Secondo runner E2E fisico (workflow nightly già presente)
- Editor UI: duplica snippet tra file con picker dedicato