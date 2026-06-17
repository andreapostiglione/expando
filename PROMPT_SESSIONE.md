# Expando — sessione compatta

**Repo:** https://github.com/andreapostiglione/expando  
**Versione:** 1.3.1 | **Release:** v1.3.1 notarized CI
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
- **D. Test** ✓ 99 test (98 pass + 1 skip E2E senza Input Monitoring)
- **v1.3.1** ✓
  - `ignore_case` per trigger
  - cache runtime (app context + secure input)
  - fast path NSWorkspace per app frontmost
  - window title lazy (solo se servono regole title)
  - `expando match --check`
  - profili risolti per app corrente

## GOAL — opzionale

- [x] Homebrew tap → v1.3.1
- [x] E2E tastiera reale (Accessibility)
  - injection reale in TextEdit (typing + clipboard)
  - pipeline E2E (build_service end-to-end)
  - global listener E2E (skip senza Input Monitoring)
  - `./scripts/run-e2e.sh`
- [x] CI: aggiornare actions Node 24 (checkout@v6, setup-python@v6, gh-release@v3)