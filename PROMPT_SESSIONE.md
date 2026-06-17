# Expando — sessione compatta

**Repo:** https://github.com/andreapostiglione/expando  
**Versione:** 1.3.2 | **Release:** v1.3.2 notarized CI  
**Team ID:** 68Q8CQBQQV (Inochi Srl Developer ID)

## Fatto

- Fasi 1–5 + review + A/B/C/D
- **B. Distrib** ✓ firmato + notarizzato via GitHub Actions (secrets configurati)
- **C. Tier 2** ✓
  - import Espanso (+ markdown/html/image_path)
  - YAML esteso, global_vars, secure input, undo, random/unicode
  - Package hub (`expando hub list/search/install/browse`)
  - UI nativa AppKit (search + form), fallback Tkinter
  - `search_terms` nel fuzzy search
- **D. Test** ✓ 99 test (97 pass + 2 skip E2E su CI headless)
- **v1.3.1** ✓
  - `ignore_case` per trigger
  - cache runtime (app context + secure input)
  - fast path NSWorkspace per app frontmost
  - window title lazy (solo se servono regole title)
  - `expando match --check`
  - profili risolti per app corrente
- **v1.3.2** ✓
  - suite E2E Accessibility (`tests/e2e`, `./scripts/run-e2e.sh`)
  - CI Node 24 (checkout@v6, setup-python@v6, gh-release@v3)
  - Homebrew tap v1.3.2
  - `ignore_case` in import Espanso

## GOAL — opzionale (v1.3.x)

Tutti completati.

## Roadmap 2026

Vedi **[ROADMAP.md](ROADMAP.md)** — prossima milestone: **v1.4 Onboarding**.

### Prossimi 3 item
- [ ] T3-01 Permission wizard (Accessibility + Input Monitoring)
- [ ] T3-02 Doctor v2
- [ ] T5-03 Localizzazione IT (doctor + wizard)