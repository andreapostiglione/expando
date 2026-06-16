# Expando — sessione compatta

**Repo:** https://github.com/andreapostiglione/expando  
**Versione:** 1.2.1 (codice) | **Release:** v1.2.1 signed DMG | notarization pending creds  
**Team ID:** 68Q8CQBQQV (Inochi Srl Developer ID)

## Fatto

- Fasi 1–5 + review + housekeeping A
- **B. Distrib (parziale)** ✓
  - App distribution bundle (`Contents/Resources/venv`, `--copies`)
  - `codesign-app.sh` Developer ID + hardened runtime
  - `notarize-dmg.sh` + `docs/RELEASE.md`
  - CI `.github/workflows/release.yml` on tag `v*`
  - DMG firmato localmente (non ancora notarizzato)

## B — ultimo step (serve credenziali Apple)

```bash
xcrun notarytool store-credentials "expando-notary" \
  --apple-id "andreapostiglione@live.it" \
  --team-id "68Q8CQBQQV" \
  --password "<app-specific-password>"

EXPANDO_NOTARIZE=1 ./scripts/build-dmg.sh
```

GitHub secrets per CI auto-release: vedi `docs/RELEASE.md`

## GOAL — prossimi

- [ ] Notarizzare DMG + staple (serve `expando-notary` keychain profile o secrets GH)
- [ ] Secrets GitHub Actions (cert p12 + notary) per CI auto-notarize
- [x] C. Tier 2: import Espanso, YAML esteso, global_vars, secure input, undo, random/unicode
- [x] D. Test listener/daemon/e2e (78 test, fake daemon fixture)