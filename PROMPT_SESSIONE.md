# Expando — sessione compatta

**Repo:** https://github.com/andreapostiglione/expando  
**Versione:** 2.5.0 | **Release:** v2.5.0 (editor form/vars, hub×8, publish)  
**Team ID:** 68Q8CQBQQV (Inochi Srl Developer ID)

## Fatto

- **v2.5.0** ✓ Sprint 4
  - T4-08 editor: form (`nome|etichetta|default`) + variabili (YAML) in UI AppKit/tk
  - T3-08 hub: 8 package (`social`, `medical-it`, `sales-it`, `support-it` + esistenti)
  - T3-09 `expando hub publish` con validazione + `--install` / `--bundle` / `--register`
  - T5-03 i18n benchmark output + marker `[installato]` su `hub list`
- **v2.4.0** ✓ Immagini + i18n + E2E self-hosted
- **Runner** ✓ `macos-MacBook-Pro-di-Inochi-2` in `~/actions-runner`
- Vedi **[ROADMAP.md](ROADMAP.md)**

## Prossimi item (Sprint 5 → v2.6.0)

- [ ] **T3-10** export/duplica snippet YAML
- [ ] **T3-05** statistiche espansioni locali (opt-in)
- [ ] **T4-09** registry plugin/snippet
- [ ] Fix test flaky (`test_when_engine`, E2E clipboard, daemon CLI)

## Backlog

- [ ] T4-10 `expando sync` assistito
- [ ] Sparkle.framework nativo in `.app`