# Expando — sessione compatta

**Repo:** https://github.com/andreapostiglione/expando  
**Versione:** 3.5.0 | **Release:** v3.5.0 (validate-community CI, doctor sync, benchmark helper latency)
**Team ID:** 68Q8CQBQQV (Inochi Srl Developer ID)

## Fatto

- **v3.5.0** ✓ Sprint 14
  - `hub validate-community` in CI
  - Doctor sync preview marketplace
  - `benchmark --sparkle` helper latency
- **v3.4.0** ✓ Sprint 13
  - `hub submit init` template
  - Doctor sezione marketplace remoto
  - `sparkle-smoke` + CI release post-build
- **v3.3.0** ✓ Sprint 12
  - `hub submit run` + `status` + `--queue`
  - Doctor hint su audit fail
  - `benchmark --sparkle`
- **v3.2.0** ✓ Sprint 11
  - 3 package community su Hub Pages
  - Trend notarization history in doctor
  - Audit firma `expando-sparkle`
- **v3.1.0** ✓ Sprint 10
  - CI E2E headless-safe (`integration` tier)
  - Marketplace URL default GitHub Pages
  - `notarize-history --json` + weekly CI cache
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

## Prossimi item (Sprint 15)

- [ ] Lint trigger duplicati cross-package in CI
- [ ] Doctor: alert package pending non sincronizzati
- [ ] Release CI benchmark Sparkle helper