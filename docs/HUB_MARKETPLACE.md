# Hub marketplace

Community hub packages can be submitted for review and listed alongside the official index.

## Submit a package

### Scaffold a new package

```bash
expando hub submit init my-package --name "My Package" --description "Short pitch"
expando hub submit init my-package -o ~/Desktop/hub-packages --tag community --tag email
```

Creates `hub.json` and a starter `snippets.yml` in `{output}/{package_id}/`. Edit both files, then run the submit workflow below.

### Validate and submit

```bash
expando hub submit ./my-package
expando hub submit run ./my-package --queue
expando hub submit status my-package
expando hub submit ./my-package -o ~/Desktop/my-package.zip --queue --json
```

Requirements:

- Folder name matches `hub.json` → `id`
- `hub.json` with `id`, `name`, `description`
- At least one valid `snippets.yml` (or `*.yml`) with `matches:`

The command validates snippets, creates a zip bundle, and prints GitHub issue instructions.

## Review flow (maintainers)

Packages in the marketplace index carry a `status`:

| Status | Visible in `hub list` |
|--------|------------------------|
| `pending` | No |
| `approved` | Yes |
| `rejected` | No |

Local queue (repo `packages/hub/marketplace.json`):

```bash
expando hub review queue ./my-package
expando hub review list
expando hub review list --status pending
expando hub review approve my-package --reviewer andrea
expando hub review reject my-package --note "duplicate of social"
```

After approval, publish into the official bundle:

```bash
expando hub publish ./my-package --bundle --register
```

## Portal (remote hosting)

Publish an approved-only JSON index for `EXPANDO_HUB_MARKETPLACE_URL`:

```bash
expando hub portal status
expando hub portal export -o ./marketplace-published.json
expando hub portal publish-site
# Default remote index (GitHub Pages); override or disable:
# export EXPANDO_HUB_MARKETPLACE_URL=https://example.com/marketplace.json
# export EXPANDO_HUB_MARKETPLACE_DISABLE=1
expando hub portal sync --dry-run
expando hub portal sync
```

`publish-site` writes `docs/hub-marketplace.html`, `docs/hub/marketplace.json`, and `docs/hub-trigger-suggestions.html` for GitHub Pages (also regenerated in `.github/workflows/pages.yml`). The marketplace page links to the trigger dashboard.

## Community packages (approved)

Approved community bundles live under `packages/community/` and are listed on GitHub Pages after review:

| ID | Description |
|----|-------------|
| `typing-it` | Indirizzo, telefono, P.IVA, CF |
| `meeting-it` | Inviti, agenda, follow-up |
| `writing-it` | Saluti e chiusure email |

```bash
expando hub install typing-it
expando hub install meeting-it
expando hub install writing-it
```

`portal sync` merges the remote index into the local queue file (`packages/hub/marketplace.json` or `EXPANDO_HUB_MARKETPLACE_PATH`).

## CI validation (maintainers)

Community packages under `packages/community/` are validated on every CI run:

```bash
expando hub validate-community
expando hub validate-community --json
expando hub validate-community --html
expando hub validate-community --html -o docs/hub-trigger-suggestions.html
```

Checks package structure, snippet validity, **cross-package duplicate literal triggers**, and **collisions with official hub packages** (community trigger already used in `default_config/match/packages/` fails CI). **Similar triggers** near official ones are reported as warnings only (fuzzy score with `prefix` / `suffix` / `contains` / `levenshtein` reason) and do not fail CI.

Export structured diagnostics from doctor:

```bash
expando doctor --full-json
expando doctor --full-json --full-output health.json
expando doctor --full-html
expando doctor --full-html --full-html-output doctor-health.html
expando doctor --doctor-json
expando doctor --doctor-json --doctor-output doctor-health.json
expando doctor --marketplace-json
expando doctor --marketplace-json -o marketplace-health.json
```

`--full-json` exports doctor, marketplace, notarization/sparkle histories, and community validation. `--full-html` writes the same snapshot as an HTML dashboard. `--doctor-json` prints the doctor payload only. `--marketplace-json` adds marketplace health (`doctor` + `marketplace`). Use `--full-output`, `--full-html-output`, `--doctor-output`, or `-o` to save reports to disk without skipping the text report.

Export pending metadata differences between remote marketplace and local queue:

```bash
expando hub portal pending-diff
expando hub portal pending-diff --json
expando hub portal pending-diff -o pending-diff.json
```

`expando doctor` shows a **metadata diff** for remote `pending` submissions (missing locally or changed fields) with hint `expando hub portal sync`.

## Official index (maintainers)

```bash
expando hub publish ./my-package --bundle --register
```

## Remote marketplace index

Set `EXPANDO_HUB_MARKETPLACE_URL` to a JSON index with the same shape as `packages/hub/index.json`.
Only entries with `"status": "approved"` (or no status field) are merged into `expando hub list`.

For a local file instead of a remote URL:

```bash
export EXPANDO_HUB_MARKETPLACE_PATH=./packages/hub/marketplace.json
expando hub list
```

Example remote index entry:

```json
{
  "id": "community-pack",
  "name": "Community Pack",
  "description": "Shared snippets",
  "author": "Contributor",
  "status": "approved",
  "submitted_at": "2026-06-17T12:00:00+00:00",
  "reviewed_at": "2026-06-17T13:00:00+00:00",
  "reviewer": "maintainer"
}
```