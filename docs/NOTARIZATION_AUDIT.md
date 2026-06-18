# Notarization audit

`expando notarize-audit` checks distribution artifacts for hardened runtime, entitlements baseline, Gatekeeper acceptance, and DMG stapling.

## Usage

```bash
expando notarize-audit
expando notarize-audit --app Expando.app --dmg Expando.dmg --strict
```

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
- Weekly workflow **Notarization audit** re-checks the latest GitHub release on the self-hosted macOS runner.