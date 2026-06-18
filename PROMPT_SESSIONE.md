# Expando — sessione compatta

**Repo:** https://github.com/andreapostiglione/expando  
**Versione:** 3.0.0 | **Release:** v3.0.0 (hub publish-site, audit history, E2E engine image)
**Team ID:** 68Q8CQBQQV (Inochi Srl Developer ID)

## Fatto

- **v3.0.0** ✓ Sprint 9
  - `expando hub portal publish-site` + Pages
  - `expando notarize-audit --record` + `notarize-history`
  - E2E engine trigger `:img` → `inject_image`
- **v2.9.0** ✓ Sprint 8
  - `expando hub portal` status/export/sync
  - `expando notarize-audit --json` + artifact CI
  - E2E image clipboard (`EXPANDO_E2E_IMAGE=1`)
- **v2.8.0** ✓ Sprint 7 (notarize-audit, E2E clipboard, hub review)
- Vedi **[ROADMAP.md](ROADMAP.md)**

## Backlog

- [ ] Fix test flaky clipboard E2E headless su macOS-latest