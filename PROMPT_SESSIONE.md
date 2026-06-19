# Expando — sessione compatta

**Repo:** https://github.com/andreapostiglione/expando  
**Versione:** 3.18.0 | **Release:** v3.18.0 (hub/index.json manifest, release health sync, Pages skip health)
**Team ID:** 68Q8CQBQQV (Inochi Srl Developer ID)

## Fatto

- **v3.18.0** ✓ Sprint 27
  - `hub/index.json` manifest su Pages
  - Release CI sync health docs su main
  - Pages preserva snapshot release (`SKIP_HEALTH`)
- **v3.17.0** ✓ Sprint 26
  - `doctor-health.html` + `hub/doctor-full.json` su Pages
  - Link health dashboard da index/maintainer/marketplace
  - CI smoke publish-site health export
- **v3.16.0** ✓ Sprint 25
  - Tabelle community validation in `doctor --full-html`
  - Badge validation su hub marketplace
  - `community-validation.json` in artifact `release-health`
- **v3.15.0** ✓ Sprint 24
  - `hub/community-validation.json` su Pages
  - Maintainer portal validation badge
  - Release artifact `release-health` unificato
- Vedi storico completo in **[ROADMAP.md](ROADMAP.md)** (Sprint 1–27)

## Prossimi sprint (loop roadmap — robustezza & completezza)

### Sprint 28 → v3.19 — Affidabilità core
- [ ] **T6-01** Listener watchdog (heartbeat, auto-restart, menu bar)
- [ ] **T6-02** Crash-loop guard launchd (backoff, safe mode)
- [ ] **T6-03** Secure-input detection nativa

### Sprint 29 → v3.20 — Doctor veritiero
- [ ] **T6-07** Injection probe live in doctor
- [ ] **T6-08** Input Monitoring gate reale
- [ ] **T6-04** `doctor --repair` PID/lock/orfani
- [ ] **T6-05** Degradation injection fail
- [ ] **T6-06** Config reload gate + rollback

### Sprint 30–35 (pianificati)
| Sprint | Versione | Tema |
|--------|----------|------|
| 30 | v3.21 | Editor avanzato + wizard DMG |
| 31 | v3.22 | Preview live, backup in-app |
| 32 | v3.23 | Sparkle parity + Homebrew auto-bump |
| 33 | v3.24 | `hub upgrade` + notifiche update |
| 34 | v3.25 | `expando health` + E2E secure-input |
| 35 | v3.26 | Auto-backup, docs, plugin allowlist (**baseline completa**) |

Dettaglio item **T6-xx** / **T7-xx** in [ROADMAP.md](ROADMAP.md) Tier 6–7.