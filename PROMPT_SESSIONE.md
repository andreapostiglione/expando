# Expando — sessione compatta

**Repo:** https://github.com/andreapostiglione/expando  
**Versione:** 2.4.0 | **Release:** v2.4.0 (image, i18n, E2E)  
**Team ID:** 68Q8CQBQQV (Inochi Srl Developer ID)

## Fatto

- **v2.4.0** ✓ Immagini + i18n + E2E
  - T4-07 campo `image:` con paste clipboard macOS
  - T5-03 i18n CLI completa (`EXPANDO_LOCALE=it|en`)
  - T5-01 workflow E2E self-hosted + docs
- **Runner self-hosted** ✓ `macos-MacBook-Pro-di-Inochi-2` online in `~/actions-runner`
  - `ENABLE_SELF_HOSTED_E2E=true` attivo
  - Workflow verde: [run 27713486348](https://github.com/andreapostiglione/expando/actions/runs/27713486348)
  - Fix CI: Python sistema + venv (no `setup-python` su macOS self-hosted)
- **v2.3.0** ✓ Templates, security-audit, i18n base
- Vedi **[ROADMAP.md](ROADMAP.md)**

## Prossimi item (Sprint 4 → v2.5.0)

- [ ] **T4-08** Editor AppKit: form + variabili in UI
- [ ] **T3-08** Hub: portare package da 4 a ≥8
- [ ] **T3-09** `expando hub publish` + validazione schema
- [ ] **T5-03** i18n residua (benchmark, hub list markers)

## Backlog

- [ ] T3-05 statistiche espansioni locali (opt-in)
- [ ] T3-10 export/duplica snippet YAML
- [ ] T4-09 registry plugin/snippet
- [ ] T4-10 `expando sync` assistito
- [ ] Fix test flaky (clipboard E2E, `test_when_engine`)
- [ ] Sparkle.framework nativo in `.app`