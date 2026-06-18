# Notarization audit

`expando notarize-audit` checks distribution artifacts for hardened runtime, entitlements baseline, Gatekeeper acceptance, and DMG stapling.

## Usage

```bash
expando notarize-audit
expando notarize-audit --app Expando.app --dmg Expando.dmg --strict
expando notarize-audit --json
expando notarize-audit -o notarize-audit.json
expando notarize-audit --record
expando notarize-history
expando notarize-history --limit 20
expando notarize-history --json
expando notarize-history -o audit-history.json
```

`--record` appends each run to `~/Library/Application Support/expando/notarize-audit-history.json` (last 100 entries). `notarize-history` shows pass/warn/fail trends over recent runs. The weekly self-hosted workflow caches history across runs and uploads it as an artifact.

Default targets:

- `Expando.app` in the repo or `/Applications/Expando.app`
- `Expando.dmg` in the repo root

## Checks

| Check | Description |
|-------|-------------|
| `codesign.verify` | Deep strict verification |
| `codesign.hardened_runtime` | Hardened runtime flag |
| `codesign.team_id` | Developer Team ID `68Q8CQBQQV` |
| `entitlements.baseline` | Match `scripts/entitlements.plist` |
| `gatekeeper.assess` | `spctl` acceptance |
| `notary.staple` | `stapler validate` on DMG |
| `sparkle.embedded` | Sparkle helper/framework in distribution builds |

## CI

- Every tagged release runs the audit after DMG creation (strict when notarization secrets exist).
- Release and weekly workflows upload `notarize-audit.json` as a GitHub Actions artifact.
- Weekly workflow **Notarization audit** re-checks the latest GitHub release on the self-hosted macOS runner.