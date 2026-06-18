# Hub marketplace

Community hub packages can be submitted for review and listed alongside the official index.

## Submit a package

```bash
expando hub submit ./my-package
expando hub submit ./my-package -o ~/Desktop/my-package.zip
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
export EXPANDO_HUB_MARKETPLACE_URL=https://andreapostiglione.github.io/expando/hub/marketplace.json
expando hub portal sync --dry-run
expando hub portal sync
```

`publish-site` writes `docs/hub-marketplace.html` and `docs/hub/marketplace.json` for GitHub Pages (also regenerated in `.github/workflows/pages.yml`).

`portal sync` merges the remote index into the local queue file (`packages/hub/marketplace.json` or `EXPANDO_HUB_MARKETPLACE_PATH`).

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