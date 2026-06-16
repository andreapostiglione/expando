<p align="center">
  <img src="assets/logo.png" alt="Expando logo" width="120" />
</p>

<h1 align="center">Expando</h1>

<p align="center">
  <strong>The privacy-first text expander for macOS.</strong><br>
  Type a trigger → get your snippet. Everywhere. Locally.
</p>

<p align="center">
  <a href="https://github.com/andreapostiglione/expando/releases/tag/v1.0.0"><img src="https://img.shields.io/badge/version-1.0.0-blue?style=flat-square" alt="Version" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License" /></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" /></a>
  <a href="https://www.apple.com/macos/"><img src="https://img.shields.io/badge/platform-macOS-000000?style=flat-square&logo=apple&logoColor=white" alt="macOS" /></a>
  <a href="https://github.com/andreapostiglione/expando/actions"><img src="https://img.shields.io/github/actions/workflow/status/andreapostiglione/expando/ci.yml?branch=main&style=flat-square&label=CI" alt="CI" /></a>
</p>

---

## What is Expando?

Expando is an open-source, system-wide text expander for macOS. Write shortcuts like `:email` or `:claude` in any app — browser, Slack, Terminal, Notes — and they expand instantly into full text, dynamic values, or shell output.

**Everything stays on your Mac.** No cloud. No account. No telemetry.

```
You type:     :claude
Expando:      claude --dangerously-skip-permissions
```

---

## Why Expando?

| | Feature | Benefit |
|---|---------|---------|
| 🔒 | **100% local** | Your snippets never leave your machine |
| 📟 | **Menu bar native** | Always-visible status, toggle, search, edit |
| 🔎 | **Search picker** | `⌘⇧E` → visual snippet browser |
| 📝 | **Forms** | Native macOS dialogs for dynamic snippets |
| 🎯 | **Per-app rules** | Different behavior in Terminal vs Safari |
| 📦 | **Packages** | Organize snippets in reusable bundles |
| 🩺 | **Built-in doctor** | Permissions, processes, config health |
| 💾 | **Backup / restore** | One-command config export |
| 🛡️ | **Shell sandbox** | Whitelist allowed shell commands |
| 🐍 | **Hackable** | Plain Python + YAML — extend in minutes |

---

## Quick start

### 1. Install

```bash
git clone https://github.com/andreapostiglione/expando.git
cd expando
./install.sh
./scripts/build-macos-app.sh
```

### 2. Grant permissions

Open **System Settings → Privacy & Security → Accessibility** and enable **Expando.app**.

Verify:

```bash
source .venv/bin/activate
expando doctor
```

### 3. Run

```bash
expando start
```

Or install auto-start at login:

```bash
./scripts/install-launch-agent.sh
```

---

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `⌥⌥` (double Alt) | Toggle Expando on/off |
| `⌘⇧E` | Open snippet search picker |
| Menu bar icon | Status, search, edit, restart, quit |

---

## CLI reference

| Command | Description |
|---------|-------------|
| `expando start` | Start background daemon |
| `expando stop` | Stop daemon |
| `expando restart` | Restart daemon |
| `expando status` | Show process status |
| `expando run` | Run in foreground (debug) |
| `expando path` | Print config directory |
| `expando list` | List all snippets |
| `expando add :trigger "text"` | Add a snippet |
| `expando import ./dir` | Import YAML files |
| `expando search` | Open snippet picker |
| `expando match :trigger` | Test-render a trigger |
| `expando edit` | Open `match/base.yml` |
| `expando doctor` | Full health check |
| `expando packages` | List installed packages |
| `expando backup` | Export config as `.tar.gz` |
| `expando restore <file>` | Restore from backup |

### Add snippet with app rules

```bash
expando add :deploy "npm run build" --if-app Terminal --if-app Cursor
```

---

## Configuration

Config lives at:

```
~/Library/Application Support/expando/
├── config/
│   ├── default.yml      # Global settings
│   └── terminal.yml     # Profile for Terminal apps
└── match/
    ├── base.yml         # Your snippets
    ├── dev.yml          # Dev shortcuts
    └── packages/
        └── core/
            └── snippets.yml
```

### Basic snippet

```yaml
matches:
  - trigger: ":email"
    replace: "you@example.com"
```

### Dynamic date

```yaml
  - trigger: ":date"
    replace: "{{today}}"
    vars:
      - name: today
        type: date
        params:
          format: "%d/%m/%Y"
```

### Shell command

```yaml
  - trigger: ":branch"
    replace: "{{output}}"
    vars:
      - name: output
        type: shell
        params:
          cmd: "git branch --show-current"
```

### Environment variables

Use `{{USER}}`, `{{HOME}}`, or `{{cwd}}` directly in any `replace` field.

```yaml
  - trigger: ":whoami"
    replace: "{{USER}} @ {{cwd}}"
```

### Interactive form

```yaml
  - trigger: ":sig"
    form:
      - name: name
        label: "Your name"
      - name: role
        label: "Your role"
    replace: |
      Best regards,
      {{name}}
      {{role}}
```

### Per-app rules

```yaml
  - trigger: ":claude"
    replace: "claude --dangerously-skip-permissions"
    if_app:
      - Terminal
      - iTerm2
      - Warp
      - Cursor
```

### Global app blacklist

In `config/default.yml`:

```yaml
app_blacklist:
  - 1Password
  - Bitwarden
```

### App profile

Create `config/terminal.yml`:

```yaml
filter:
  app_names:
    - Terminal
    - iTerm2
    - Warp
    - Cursor

search_shortcut: CMD+SHIFT+E

shell_allowlist:
  - echo
  - git
  - pwd
  - whoami
```

---

## Packages

Drop snippet bundles into `match/packages/<name>/`. Expando loads them automatically.

```bash
expando packages    # list installed packages
expando import ./my-snippets/
```

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Expando.app / expando daemon                   │
├─────────────────────────────────────────────────┤
│  Menu bar (rumps)  │  Keyboard listener (pynput)│
├────────────────────┴────────────────────────────┤
│  Expansion engine                               │
│  ├── Trigger buffer                             │
│  ├── App context filter                         │
│  ├── Form dialogs (osascript)                   │
│  └── Renderer (date / shell / env / clipboard)  │
├─────────────────────────────────────────────────┤
│  YAML config (watchdog auto-reload)             │
│  config/ + match/ + match/packages/             │
└─────────────────────────────────────────────────┘
```

---

## Build & distribute

```bash
./scripts/build-macos-app.sh   # Build Expando.app
./scripts/build-dmg.sh         # Create Expando.dmg
```

### Homebrew

```bash
brew install andreapostiglione/tap/expando
```

---

## Development

```bash
git clone https://github.com/andreapostiglione/expando.git
cd expando
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

### Project structure

```
expando/
├── src/expando/          # Core Python package
│   ├── cli.py            # Command-line interface
│   ├── engine.py         # Expansion engine
│   ├── listener.py       # Keyboard service
│   ├── menubar.py        # macOS menu bar
│   ├── forms.py          # Native form dialogs
│   ├── search.py         # Snippet picker
│   ├── profiles.py       # Per-app config profiles
│   └── packages.py       # Package loader
├── tests/                # 25 pytest tests
├── scripts/              # Install, build, launch agent
├── default_config/       # Default YAML templates
└── assets/               # Logo and branding
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Snippets don't expand | Run `expando doctor`, check Accessibility permission |
| `python3.14` in Privacy settings | Run `./scripts/build-macos-app.sh`, grant permission to **Expando.app** |
| Multiple instances running | `expando stop` then restart LaunchAgent |
| Config not reloading | Check `auto_restart: true` in `config/default.yml` |

```bash
expando doctor    # always start here
```

Logs: `~/Library/Application Support/expando/expando.log`

---

## Contributing

Contributions welcome. Fork the repo, create a branch, add tests, open a PR.

1. `pip install -e ".[dev]"`
2. `pytest -q`
3. Keep changes focused and documented

---

## Author

**Andrea Postiglione** — [github.com/andreapostiglione](https://github.com/andreapostiglione)

---

## License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <sub>Built with Python. Designed for macOS. Owned by you.</sub>
</p>