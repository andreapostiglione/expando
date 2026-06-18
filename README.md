<p align="center">
  <img src="assets/logo.png" alt="Expando logo" width="120" />
</p>

<h1 align="center">Expando</h1>

<p align="center">
  <strong>The privacy-first text expander for macOS.</strong><br>
  Type a trigger → get your snippet. Everywhere. Locally.
</p>

<p align="center">
  <a href="https://github.com/andreapostiglione/expando/releases/tag/v3.11.0"><img src="https://img.shields.io/badge/version-3.11.0-blue?style=flat-square" alt="Version" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License" /></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" /></a>
  <a href="https://www.apple.com/macos/"><img src="https://img.shields.io/badge/platform-macOS-000000?style=flat-square&logo=apple&logoColor=white" alt="macOS" /></a>
  <a href="https://github.com/andreapostiglione/expando/actions"><img src="https://img.shields.io/github/actions/workflow/status/andreapostiglione/expando/ci.yml?branch=main&style=flat-square&label=CI" alt="CI" /></a>
</p>

---

## What's new (v3.7)

Recent releases focused on the **hub marketplace**, **release quality**, and **diagnostics**:

| Version | Highlights |
|---------|------------|
| **v3.11** | Trigger dashboard on GitHub Pages (`publish-site`) · `doctor --doctor-json` · Sparkle benchmark SVG trend in release artifact |
| **v3.10** | Trigger suggestions HTML dashboard · doctor text + marketplace JSON · `EXPANDO_SPARKLE_HELPER_STRICT` release CI |
| **v3.9** | Fuzzy trigger score/reason in `validate-community` · `doctor --marketplace-json` · `--sparkle-fail-ms` + sparkline trend |
| **v3.8** | Trigger similarity warnings in `validate-community` · `hub portal pending-diff` JSON export · `sparkle-benchmark-history` release artifact |
| **v3.7** | Community vs official trigger lint · doctor pending metadata diff · `SPARKLE_HELPER_SLOW` warning in release CI (15s threshold) |
| **v3.6** | Cross-package trigger lint in CI · doctor alert for unsynced remote pending submissions · Sparkle benchmark artifact on release |
| **v3.5** | `hub validate-community` in CI · doctor marketplace sync preview · `benchmark --sparkle` helper latency |
| **v3.4** | `hub submit init` scaffold · doctor remote marketplace section · `sparkle-smoke` + release CI smoke test |
| **v3.3** | `hub submit run` / `status` · doctor notarization hint · `benchmark --sparkle` |
| **v3.2** | 3 approved community packages on Hub Pages · notarization history in doctor · Sparkle helper signing audit |
| **v3.1** | Default GitHub Pages marketplace URL · headless-safe CI E2E · `notarize-history --json` |
| **v3.0** | `hub portal publish-site` · `notarize-audit --record` · E2E image trigger (`:img`) |

Community packages (install via `expando hub install`): `typing-it`, `meeting-it`, `writing-it`.  
Hub marketplace site: [andreapostiglione.github.io/expando/hub-marketplace.html](https://andreapostiglione.github.io/expando/hub-marketplace.html)

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
| 🔎 | **Fuzzy search** | `⌘⇧E` → live filter + preview panel |
| 📝 | **Multi-field forms** | Single-window input for dynamic snippets |
| 🎯 | **Advanced app rules** | Filter by app name, bundle ID, or window title |
| 📦 | **Packages** | Organize snippets in reusable bundles |
| 🩺 | **Built-in doctor** | Permissions, marketplace sync, notarization history |
| 📡 | **Hub marketplace** | Community packages, submit/review workflow, GitHub Pages |
| ✨ | **Native Sparkle updates** | Signed DMG, appcast, helper smoke test in release CI |
| 💾 | **Backup / restore** | One-command config export |
| 🛡️ | **Shell sandbox** | Whitelist allowed shell commands |
| 🐍 | **Hackable** | Plain Python + YAML — extend in minutes |

---

## Quick start

### 1. Install

**DMG (recommended):** download [Expando.dmg](https://github.com/andreapostiglione/expando/releases/latest) from GitHub Releases.

**Homebrew cask:**

```bash
brew tap andreapostiglione/tap
brew install --cask expando
```

**From source:**

```bash
git clone https://github.com/andreapostiglione/expando.git
cd expando
./install.sh
./scripts/build-macos-app.sh
```

Website: [andreapostiglione.github.io/expando](https://andreapostiglione.github.io/expando/)

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
| `expando setup` | Permission onboarding wizard (macOS) |
| `expando editor` | Graphical snippet editor (AppKit on macOS) |
| `expando check-updates` | Check Sparkle appcast for new releases |
| `expando plugins list` | List loaded Python plugins |
| `expando migrate-espanso` | Import Espanso config with auto backup |
| `expando migrate-textexpander` | Import TextExpander CSV or Settings.textexpander |
| `expando migrate-raycast --source file.json` | Import Raycast snippets JSON export |
| `expando new :trigger --template email` | Create snippet from built-in template |
| `expando templates list` | List available snippet templates |
| `expando benchmark` | Benchmark trigger buffer under load (1000+ matches) |
| `expando benchmark --sparkle` | Benchmark appcast fetch + Sparkle helper update-check latency |
| `expando benchmark --sparkle --sparkle-warn-ms 15000` | Same + `SPARKLE_HELPER_SLOW` when helper exceeds threshold |
| `expando benchmark --sparkle --sparkle-fail-ms 30000` | Exit 1 + `SPARKLE_HELPER_FAIL` when helper exceeds fail threshold |
| `expando sparkle-smoke --app Expando.app` | Verify Sparkle helper codesign + framework embed |
| `expando sparkle-benchmark-history` | Show Sparkle helper latency history across releases |
| `expando sparkle-benchmark-history record` | Run Sparkle benchmark and append to `sparkle-benchmark-history.json` |
| `expando notarize-audit` | Audit codesign, entitlements, Gatekeeper, notarization staples |
| `expando notarize-audit --record` | Append audit run to local `notarize-audit-history.json` |
| `expando notarize-history` | Show recent notarization audit runs |
| `expando security-audit` | Review shell allowlist, imports, and hub TLS |
| `expando sync` | Assisted iCloud config linking (see [docs/SYNC.md](docs/SYNC.md)) |
| Snippet `image:` field | Paste PNG/JPEG from config dir (fallback to `replace` text) |
| `expando crashes list` | List local crash reports (never uploaded) |
| `expando logs` | Show recent log lines |
| `expando logs --tail` | Follow log file (debug) |
| `expando packages` | List installed packages |
| `expando backup` | Export config as `.tar.gz` |
| `expando restore <file>` | Restore from backup |

### Add snippet with app rules

```bash
expando add :deploy "npm run build" --if-app Terminal --if-app Cursor
```

### Migrate from other expanders

```bash
# Espanso (auto-detects ~/Library/Application Support/espanso)
expando migrate-espanso

# TextExpander CSV export or live Settings.textexpander
expando migrate-textexpander
expando migrate-textexpander --source ~/Downloads/email-snippets.csv

# Raycast: run "Export Snippets" in Raycast, then:
expando migrate-raycast --source ~/Downloads/snippets.json
```

Each `migrate-*` command creates a config backup and prints a report (imported, skipped, warnings).

### Hub & marketplace CLI

| Command | Description |
|---------|-------------|
| `expando hub list` | List official + approved community packages |
| `expando hub install <id>` | Install a hub package into your config |
| `expando hub publish ./pkg` | Validate, bundle, optionally register a local package |
| `expando hub validate-community` | Validate `packages/community/` (CI pre-submit gate) |
| `expando hub validate-community --html` | Write trigger similarity dashboard HTML |
| `expando hub submit init <id>` | Scaffold `hub.json` + `snippets.yml` for a new package |
| `expando hub submit run ./pkg` | Validate, zip, print GitHub issue instructions |
| `expando hub submit status <id>` | Marketplace review status for a submission |
| `expando hub portal status` | Local vs remote marketplace index stats |
| `expando hub portal sync` | Merge remote marketplace JSON into local queue |
| `expando hub portal publish-site` | Regenerate Hub Pages HTML + JSON + trigger dashboard |
| `expando hub portal pending-diff` | Export remote vs local pending metadata diff (JSON) |
| `expando doctor --doctor-json` | Export structured doctor diagnostics JSON |
| `expando doctor --marketplace-json` | Export marketplace health JSON (community, sync, pending diff) |
| `expando hub review list` | List pending/approved/rejected queue (maintainers) |
| `expando hub review approve <id>` | Approve a queued package (maintainers) |

`expando doctor` includes: notarization audit history trend, remote marketplace community packages, sync dry-run stats, and pending-submission alerts.

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

  - trigger: ":readme"
    replace: "# README"
    if_title:
      - README
    if_bundle:
      - com.todesktop
```

Supported filters per match: `if_app`, `unless_app`, `if_bundle`, `unless_bundle`, `if_title`, `unless_title`.

### Global app blacklist

In `config/default.yml`:

```yaml
app_blacklist:
  - 1Password
  - Bitwarden
```

### Block notifications & logging

When expansion is blocked (password field, app rules, or shell deny), Expando shows a macOS notification toast. Configure in `config/default.yml`:

```yaml
notify_on_block: true
notify_cooldown_seconds: 30
log_level: INFO   # or DEBUG; override with EXPANDO_LOG_LEVEL
```

View logs:

```bash
expando logs          # last 50 lines
expando logs -n 200   # last 200 lines
expando logs --tail   # follow (Ctrl+C to stop)
```

Logs are written to `~/Library/Application Support/expando/expando.log` with automatic rotation.

### Plugins & script variables (v2.0)

Drop Python hooks in `~/Library/Application Support/expando/plugins/`:

```python
def before_expand(context): ...
def transform_replacement(text, context): return text
def run(context): return "dynamic value"  # for script vars
```

Script variable in YAML:

```yaml
vars:
  - name: tag
    type: script
    params:
      path: example.py
```

See [docs/PLUGINS.md](docs/PLUGINS.md).

### Conditional matches (`when:`)

```yaml
matches:
  - trigger: ":hi"
    replace: "Good morning"
    when:
      hour: "5-12"
  - trigger: ":hi"
    replace: "Good evening"
    when:
      hour: "17-24"
```

Supported keys: `app`, `bundle`, `hour`, `weekday`, `env`, `form`.

Optional config sync: [docs/SYNC.md](docs/SYNC.md).

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

## Packages & hub marketplace

Drop snippet bundles into `match/packages/<name>/`. Expando loads them automatically.

```bash
expando packages              # list installed packages
expando hub list              # official + approved community packages
expando hub search email      # search hub packages
expando hub install core      # install an official package
expando hub install typing-it # community: address, phone, tax IDs (IT)
expando hub install meeting-it
expando hub install writing-it
expando hub browse            # visual package picker (AppKit on macOS)
expando import ./my-snippets/
```

The official index lives in `packages/hub/index.json`. Approved community packages are merged from the remote marketplace (default: [GitHub Pages JSON](https://andreapostiglione.github.io/expando/hub/marketplace.json)). Override with `EXPANDO_HUB_INDEX_URL` or `EXPANDO_HUB_MARKETPLACE_URL`; disable remote with `EXPANDO_HUB_MARKETPLACE_DISABLE=1`.

Full guide: [docs/HUB_MARKETPLACE.md](docs/HUB_MARKETPLACE.md)

### Contribute a community package

```bash
# 1. Scaffold a new package folder
expando hub submit init my-package --name "My Package" -o ~/hub-packages

# 2. Edit hub.json + snippets.yml, then validate and bundle
expando hub validate-community    # CI gate: structure + cross-package trigger lint
expando hub submit run ~/hub-packages/my-package --queue
expando hub submit status my-package

# Maintainer review (local queue)
expando hub review list --status pending
expando hub review approve my-package --reviewer you
expando hub portal publish-site   # regenerate docs/hub-marketplace.html + JSON + trigger dashboard
```

`expando doctor` shows remote marketplace packages, sync dry-run stats (added/updated/unchanged), and alerts when remote **pending** submissions are missing from the local queue (`expando hub portal sync`).

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
│  ├── App context filter (name / bundle / title) │
│  ├── Native UI (fuzzy search + multi-field form)│
│  └── Renderer (date / shell / env / clipboard)  │
├─────────────────────────────────────────────────┤
│  YAML config (watchdog auto-reload)             │
│  config/ + match/ + match/packages/             │
└─────────────────────────────────────────────────┘
```

---

## Build & distribute

```bash
./scripts/build-macos-app.sh                        # Dev build (uses repo .venv)
EXPANDO_DISTRIBUTION=1 EXPANDO_SIGN=1 ./scripts/build-dmg.sh   # Signed release DMG
EXPANDO_NOTARIZE=1 ./scripts/build-dmg.sh           # + Apple notarization (after setup)
```

Signing uses your **Developer ID Application** certificate. Notarization and CI secrets: see [docs/RELEASE.md](docs/RELEASE.md).

Pushing a `v*` tag triggers GitHub Actions to:

1. Build and sign `Expando.dmg` (notarize when secrets are set)
2. Run `expando notarize-audit` and upload the JSON report
3. Run `expando sparkle-smoke` and `expando benchmark --sparkle` (benchmark uploaded as artifact)
4. Generate Sparkle `appcast.xml` and attach both to the GitHub Release
5. Commit the updated appcast to `main`

### Homebrew

Tap: [andreapostiglione/homebrew-tap](https://github.com/andreapostiglione/homebrew-tap) (`andreapostiglione/tap`).

```bash
brew tap andreapostiglione/tap
brew install expando
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
./scripts/run-e2e.sh   # macOS E2E (Accessibility; Input Monitoring for global listener)
```

### Project structure

```
expando/
├── src/expando/          # Core Python package
│   ├── cli.py            # Command-line interface
│   ├── engine.py         # Expansion engine
│   ├── listener.py       # Keyboard service
│   ├── menubar.py        # macOS menu bar
│   ├── forms.py          # Multi-field form UI
│   ├── search.py         # Fuzzy snippet picker
│   ├── fuzzy.py          # Fuzzy match scoring
│   ├── ui_native.py      # Tkinter search + form windows
│   ├── profiles.py       # Per-app config profiles
│   └── packages.py       # Package loader
├── tests/                # 227+ pytest tests (incl. tests/e2e)
├── packages/
│   ├── hub/              # Official hub index + marketplace queue
│   └── community/        # Approved community snippet bundles
├── docs/                 # HUB_MARKETPLACE, RELEASE, PLUGINS, SYNC, …
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
expando doctor              # permissions, config, marketplace, notarization history
expando notarize-history    # recent signed-build audit runs (maintainers)
```

Logs: `~/Library/Application Support/expando/expando.log`

---

## Roadmap

Current baseline: **v3.7.0**. See [ROADMAP.md](ROADMAP.md) for completed sprints and Sprint 17+ backlog.

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