# Release & notarization

## Local build (signed DMG)

Distribution builds embed `Python.framework` into `Expando.app`. Install a framework
Python 3.12 locally before building:

```bash
brew install python@3.12
```

```bash
chmod +x scripts/*.sh
EXPANDO_DISTRIBUTION=1 EXPANDO_SIGN=1 EXPANDO_NOTARIZE=0 ./scripts/build-dmg.sh
```

## Notarization (one-time setup)

Store credentials in Keychain:

```bash
xcrun notarytool store-credentials "expando-notary" \
  --apple-id "your@email.com" \
  --team-id "YOURTEAMID" \
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
| `APPLE_SIGNING_IDENTITY` | e.g. `Developer ID Application: Example Org (YOURTEAMID)` |
| `NOTARY_APPLE_ID` | Apple ID email |
| `NOTARY_PASSWORD` | App-specific password |
| `NOTARY_TEAM_ID` | Apple Developer Team ID |
| `EXPANDO_SPARKLE_PUBLIC_ED_KEY` | Sparkle EdDSA public key for `SUPublicEDKey` |
| `SPARKLE_PRIVATE_KEY` | Sparkle EdDSA private key PEM for appcast signing |

Optional API key alternative: `NOTARY_API_KEY`, `NOTARY_API_KEY_ID`, `NOTARY_API_ISSUER`.

## Sparkle appcast

Each release generates `appcast.xml` (Sparkle-compatible feed) and attaches it to the GitHub release.

Sparkle signing is required for production release appcasts. `scripts/generate-appcast.sh`
fails without `SPARKLE_PRIVATE_KEY` unless `EXPANDO_ALLOW_UNSIGNED_APPCAST=1` is set for
local unsigned test feeds.

Local generation:

```bash
chmod +x scripts/generate-appcast.sh
SPARKLE_PRIVATE_KEY="$(cat ed_private_key.pem)" ./scripts/generate-appcast.sh 1.6.0 Expando.dmg appcast.xml
```

Feed URL (default): `https://raw.githubusercontent.com/andreapostiglione/expando/main/appcast.xml`

## Homebrew cask

Prebuilt DMG install:

```bash
brew install --cask andreapostiglione/tap/expando
```

Update `Casks/expando.rb` in the tap with version + DMG `sha256` after each release.
Do not add a `python@3.12` cask dependency; the public app bundle is self-contained.

### Export certificate

1. Keychain Access → My Certificates → Developer ID Application
2. Export as `.p12`
3. `base64 -i certificate.p12 | pbcopy`
4. Add as `APPLE_CERTIFICATE_BASE64` in GitHub repo secrets
