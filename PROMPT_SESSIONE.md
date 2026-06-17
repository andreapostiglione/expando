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
- **D. Test** ✓ 93 test (listener/daemon/CLI/hub)
- **v1.3.1** ✓
  - `ignore_case` per trigger
  - cache runtime (app context + secure input)
  - fast path NSWorkspace per app frontmost
  - window title lazy (solo se servono regole title)
  - `expando match --check`
  - profili risolti per app corrente

## GOAL — opzionale

- [ ] Homebrew tap → v1.3.1
- [ ] E2E tastiera reale (Accessibility)
- [ ] CI: aggiornare actions Node 24