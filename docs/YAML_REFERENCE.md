# YAML configuration reference

Expando configuration lives under your config directory (default:
`~/Library/Application Support/expando` on macOS).

## Layout

```
config/
  default.yml          # Global app settings
  terminal.yml         # Optional profile overrides
match/
  base.yml             # Snippets
  dev.yml
  packages/            # Installed hub packages
plugins/
  *.py                 # Local Python plugins
```

## `config/default.yml` — app settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `toggle_key` | string | `ALT` | Double-tap modifier to enable/disable (`OFF` disables) |
| `backend` | string | `auto` | Injection backend: `auto`, `inject`, `clipboard` |
| `auto_restart` | bool | `true` | Reload snippets when YAML files change |
| `clipboard_threshold` | int | `100` | Paste via clipboard when replacement is longer |
| `max_regex_buffer_size` | int | `30` | Max typed buffer for regex triggers |
| `enabled` | bool | `true` | Start with expansion enabled |
| `app_blacklist` | list | `[]` | App names where Expando is disabled |
| `shell_allowlist` | list | `[]` | Allowed executables for `shell` variables (empty = deny all) |
| `search_shortcut` | string | `CMD+SHIFT+E` | Open snippet search |
| `undo_shortcut` | string | `CMD+SHIFT+Z` | Undo last expansion |
| `respect_secure_input` | bool | `true` | Block expansion in password fields |
| `notify_on_block` | bool | `true` | Toast when expansion is blocked |
| `notify_cooldown_seconds` | int | `30` | Minimum seconds between block toasts |
| `log_level` | string | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `check_updates` | bool | `true` | Daily Sparkle / appcast check from menu bar |
| `update_feed_url` | string | *(built-in)* | Override appcast URL |
| `track_expansions` | bool | `false` | Opt-in local expansion counters |
| `plugins_allowlist` | list | `[]` | If set, only listed `plugins/*.py` files load |
| `auto_backup` | string | `weekly` | Scheduled backup on daemon start: `off`, `daily`, `weekly` |
| `auto_backup_retention` | int | `7` | Keep last N automatic backups |
| `auto_backup_stale_days` | int | `14` | `expando doctor` warns if backup is older |

## Match files (`match/*.yml`)

Each file contains optional `global_vars` and a `matches` list.

### Match fields

| Key | Type | Description |
|-----|------|-------------|
| `trigger` / `triggers` | string / list | Literal or regex trigger text |
| `replace` | string | Expanded text (supports variables) |
| `regex` | bool | Treat trigger as regular expression |
| `word_break` | bool | Require word boundary after trigger |
| `ignore_case` | bool | Case-insensitive literal trigger |
| `vars` | list | Per-snippet variables |
| `form` | list | Interactive form fields |
| `if_app` / `unless_app` | list | Restrict to app names |
| `if_bundle` / `unless_bundle` | list | Restrict to bundle IDs |
| `if_title` / `unless_title` | list | Restrict to window title substrings |
| `when` | object | Structured conditions (time, weekday, etc.) |
| `priority` | int | Higher wins on duplicate triggers |
| `propagate_case` | bool | Match typed letter case |
| `trim` | bool | Trim replacement whitespace |
| `force_clipboard` | bool | Always inject via clipboard |
| `image` | string | Path to PNG for image snippets |
| `label` | string | Display name in search |
| `search_terms` | list | Extra search keywords |

### Variable types

| Type | Params | Description |
|------|--------|-------------|
| `plain` | `value` | Static text |
| `shell` | `cmd` | Shell command (requires `shell_allowlist`) |
| `script` | `path` | Python plugin under `plugins/` |
| `form` | — | References `form` field by name |

## Profiles

`config/<app>.yml` merges over `default.yml` when the frontmost app matches
(profile resolution is handled by `profiles.py`).

## Runtime files (not synced)

These are written under the config directory and excluded from git/iCloud sync:

- `expando.pid`, `expando.lock`, `expando.log`
- `runtime-health.json`, `crash-loop.json`, `backups/`
- `crashes/`, `expansion_stats.json`

## Examples

```yaml
# match/dev.yml
matches:
  - trigger: ":addr"
    replace: "123 Main St"
    if_app:
      - Mail
  - trigger: ":date"
    replace: "{{mydate}}"
    vars:
      - name: mydate
        type: shell
        params:
          cmd: date +%Y-%m-%d
```

```yaml
# config/default.yml
plugins_allowlist:
  - example.py
auto_backup: daily
shell_allowlist:
  - date
  - echo
```