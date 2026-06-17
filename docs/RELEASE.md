# Release & notarization

## Local build (signed DMG)

```bash
chmod +x scripts/*.sh
EXPANDO_DISTRIBUTION=1 EXPANDO_SIGN=1 EXPANDO_NOTARIZE=0 ./scripts/build-dmg.sh
```

## Notarization (one-time setup)

Store credentials in Keychain:

```bash
xcrun notarytool store-credentials "expando-notary" \
  --apple-id "your@email.com" \
  --team-id "68Q8CQBQQV" \
  --password "xxxx-xxxx-xxxx-xxxx"
```

Then build with notarization:

```bash
EXPANDO_NOTARIZE=1 ./scripts/build-dmg.sh
```

Or use App Store Connect API key env vars: `NOTARY_API_KEY`, `NOTARY_API_KEY_ID`, `NOTARY_API_ISSUER`.

## GitHub Actions (automatic on tag)

Push a tag `v*` to trigger `.github/workflows/release.yml`.

### Required secrets

| Secret | Description |
|--------|-------------|
| `APPLE_CERTIFICATE_BASE64` | Developer ID .p12 exported from Keychain, base64-encoded |
| `APPLE_CERTIFICATE_PASSWORD` | Password for the .p12 export |
| `APPLE_SIGNING_IDENTITY` | e.g. `Developer ID Application: Inochi Srl (68Q8CQBQQV)` |
| `NOTARY_APPLE_ID` | Apple ID email |
| `NOTARY_PASSWORD` | App-specific password |
| `NOTARY_TEAM_ID` | `68Q8CQBQQV` |

Optional API key alternative: `NOTARY_API_KEY`, `NOTARY_API_KEY_ID`, `NOTARY_API_ISSUER`.

## Sparkle appcast

Each release generates `appcast.xml` (Sparkle-compatible feed) and attaches it to the GitHub release.

Optional secret for EdDSA signatures:

| Secret | Description |
|--------|-------------|
| `SPARKLE_PRIVATE_KEY` | EdDSA private key PEM for `sign_update` |

Local generation:

```bash
chmod +x scripts/generate-appcast.sh
./scripts/generate-appcast.sh 1.6.0 Expando.dmg appcast.xml
```

Feed URL (default): `https://raw.githubusercontent.com/andreapostiglione/expando/main/appcast.xml`

## Homebrew cask

Prebuilt DMG install:

```bash
brew install --cask andreapostiglione/tap/expando
```

Update `Casks/expando.rb` in the tap with version + DMG `sha256` after each release.

### Export certificate

1. Keychain Access → My Certificates → Developer ID Application
2. Export as `.p12`
3. `base64 -i certificate.p12 | pbcopy`
4. Add as `APPLE_CERTIFICATE_BASE64` in GitHub repo secrets