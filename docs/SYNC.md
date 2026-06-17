# Optional config sync (v2.0)

Expando has no built-in cloud sync. Use the assisted CLI or sync manually.

## Assisted CLI (v2.7+)

```bash
expando sync status
expando sync init-git --commit
expando sync icloud --dry-run
expando sync icloud
```

`init-git` writes a safe `.gitignore` (skips pid/log/stats). `icloud` copies `config/`, `match/`, and `plugins/` into iCloud Drive and symlinks the default config path.

## Git (manual)

```bash
cd ~/Library/Application\ Support/expando
git init
git add config match plugins
git commit -m "Expando snippets"
# push to a private repo
```

On another Mac: clone into the same path, then `expando restart`.

## iCloud Drive (manual)

```bash
mv ~/Library/Application\ Support/expando ~/Library/Mobile\ Documents/com~apple~CloudDocs/expando-config
ln -s ~/Library/Mobile\ Documents/com~apple~CloudDocs/expando-config \
  ~/Library/Application\ Support/expando
```

Keep one Mac as the primary editor to avoid YAML merge conflicts.

## What to sync

| Path | Sync? |
|------|-------|
| `config/` | yes |
| `match/` | yes |
| `plugins/` | yes |
| `expando.log`, `*.pid` | no |