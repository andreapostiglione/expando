# Expando — sessione compatta

**Repo:** https://github.com/andreapostiglione/expando  
**Versione:** 3.1.0 | **Release:** v3.1.0 (CI E2E tiers, marketplace default URL, audit history JSON)
**Team ID:** 68Q8CQBQQV (Inochi Srl Developer ID)

## Fatto

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

## Prossimi item (Sprint 11)

- [ ] Primi package community approvati su Hub Pages
- [ ] Trend notarization history in doctor
- [ ] Sparkle helper signing audit automatico