# Expando — sessione compatta

**Repo:** https://github.com/andreapostiglione/expando  
**Versione:** 1.6.0 | **Release:** v1.6.0 (in preparazione)
**Team ID:** 68Q8CQBQQV (Inochi Srl Developer ID)

## Fatto

- Fasi 1–5 + review + A/B/C/D + Tier 3 parziale
- **v1.6.0** ✓ Distribuzione
  - T3-11 Sparkle appcast + `expando check-updates` + menu bar
  - T3-12 Homebrew cask (`brew install --cask expando`)
  - T3-13 Sito GitHub Pages (`docs/index.html`)
  - T3-14 What's new al primo avvio post-update
- **v1.5.0** ✓ Editor & contenuti
  - T3-06 Snippet editor AppKit (`expando editor`, menu bar)
  - T3-07 Migrazione Espanso (`expando migrate-espanso` + backup auto)
  - T3-08 Hub: `dev`, `email-it`, `legal-it`
- **v1.4.1** ✓ Affidabilità
  - T3-03 Notifiche contestuali (secure input, `if_app`, shell deny)
  - T3-04 Log strutturato (`expando logs`, `--tail`, rotazione, `log_level`)
  - T5-01 CI self-hosted E2E (workflow + `EXPANDO_E2E_FULL=1`)
- **v1.4.0** ✓ Onboarding
  - T3-01 Permission wizard (`expando setup`, primo avvio)
  - T3-02 Doctor v2 (runtime app/python, injection, TCC input)
  - T5-03 Localizzazione IT (doctor + wizard)
- **v1.3.2** ✓ E2E, CI Node 24, Homebrew
- Vedi **[ROADMAP.md](ROADMAP.md)** per v1.5+

## Prossimi item (v2.0)

- [ ] T4-01 Plugin API
- [ ] T4-02 Variable type `script`
- [ ] T4-03 Conditional matches