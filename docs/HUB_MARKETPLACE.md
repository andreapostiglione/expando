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

## Official index (maintainers)

```bash
expando hub publish ./my-package --bundle --register
```

## Remote marketplace index

Set `EXPANDO_HUB_MARKETPLACE_URL` to a JSON index with the same shape as `packages/hub/index.json`.
`expando hub list` merges community packages that are not already in the official index.

Example:

```bash
export EXPANDO_HUB_MARKETPLACE_URL=https://example.com/expando-hub/index.json
expando hub list
```