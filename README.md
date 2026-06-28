<p align="center">
  <img src="assets/logo.png" alt="Expando logo" width="120" />
</p>

<h1 align="center">Expando</h1>

<p align="center">
  <strong>The privacy-first text expander for macOS.</strong><br>
  Type a trigger → get your snippet. Everywhere. Locally.
</p>

<p align="center">
  <a href="https://github.com/andreapostiglione/expando/releases/tag/v3.29.11"><img src="https://img.shields.io/badge/version-3.29.11-blue?style=flat-square" alt="Version" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License" /></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" /></a>
  <a href="https://www.apple.com/macos/"><img src="https://img.shields.io/badge/platform-macOS-000000?style=flat-square&logo=apple&logoColor=white" alt="macOS" /></a>
  <a href="https://github.com/andreapostiglione/expando/actions"><img src="https://img.shields.io/github/actions/workflow/status/andreapostiglione/expando/ci.yml?branch=main&style=flat-square&label=CI" alt="CI" /></a>
</p>

---

## What's new

Full history: **[CHANGELOG.md](CHANGELOG.md)** · [GitHub Releases](https://github.com/andreapostiglione/expando/releases)

### Release status

The current public build is ready for normal macOS users:

- `Expando.dmg` is Developer ID signed, notarized, stapled, and accepted by Gatekeeper.
- `Expando.app` inside the DMG passes deep codesign verification.
- `appcast.xml` is signed for Sparkle updates.
- Homebrew cask `andreapostiglione/tap/expando` points to the same verified DMG.

### v3.29.11 — Sparkle helper runtime fix (latest)

| Area | What's new |
|------|------------|
| **Sparkle** | Helper links with bundle-local framework RPATH, so it can load `Sparkle.framework` at runtime |
| **Release** | Distribution verification fails if the helper is missing the Sparkle RPATH |

### v3.29.10 — Runtime launch fix

| Area | What's new |
|------|------------|
| **Runtime** | Distribution launcher uses Python 3.12 explicitly, matching bundled native PyObjC wheels |
| **Homebrew** | Cask generators declare `python@3.12` as a dependency |
| **Release** | Bundle verification imports PyObjC and `pynput.keyboard` before a DMG is shipped |

### v3.29.9 — LaunchAgent bundle fix

| Area | What's new |
|------|------------|
| **Autostart** | Bundled LaunchAgent startup resolves the installed app executable instead of falling back to a source-style venv |
| **Release** | Distribution verification now checks the bundled launch script before notarized DMGs are shipped |

### v3.29.8 — Editor UI cleanup

| Area | What's new |
|------|------------|
| **Snippet editor** | Reworked native AppKit layout to remove overlapping labels and fields |
| **Editing** | Text areas stay editable after loading snippets instead of being restyled as read-only |
| **Selection** | Snippet list selection now updates the details panel through the correct AppKit delegate |
| **Tests** | AppKit coverage checks text editability and direct-control frame overlap |

### v3.29.7 — Snippet creation UX

| Area | What's new |
|------|------------|
| **Menu bar** | Direct **New snippet** action opens the editor already in create mode |
| **Editor** | New-snippet mode starts blank and clears advanced fields before saving |
| **Tests** | UI bridge and editor coverage for menu-driven snippet creation |

### v3.29.6 — Production hardening

| Area | What's new |
|------|------------|
| **Menu bar** | Runtime health in one click · snooze 1h/4h · 🔒 badge when permissions missing |
| **Hub** | Upgrade packages from menu bar with YAML diff preview before applying |
| **Wizard** | Live permission badges for Accessibility + Input Monitoring |
| **Repair** | `expando doctor --repair` reinstalls outdated LaunchAgent plist |
| **Release** | Distribution bundles verify runtime assets; DMG container and app bundle are signed/notarized; Sparkle appcast and Homebrew cask are verified; live TextEdit E2E is opt-in |

### v3.28 — Stability hardening

Production-focused reliability for the daemon, listener, and menu bar:

| Area | What's improved |
|------|-----------------|
| **Listener** | Watchdog retries every 30s if pynput dies — no permanent dead listener |
| **Engine** | Lock released before render/inject/undo — fixes freeze with form snippets + menu bar |
| **Restart** | Menu bar restart waits for old PID to exit — no duplicate listeners |
| **Crash recovery** | Crash reports feed `crash-loop.json`; safe mode + `doctor --repair` clears it |
| **Config reload** | Waits for stable YAML files; last-good snapshot before applying changes |
| **Daemon start** | Fails clearly if pid file never appears (no fake parent pid) |
| **Permissions** | macOS notification on startup when Accessibility or Input Monitoring is missing |
| **State files** | Atomic JSON writes for health, crash-loop, injection-health |
| **LaunchAgent** | `ThrottleInterval` 15s to avoid crash-loop respawn storms |

**390** passing automated tests (+ 8 opt-in/skipped E2E checks). Runtime permissions are required for **Expando.app** when installed from the DMG/Homebrew cask, or for the Python runtime reported by `expando doctor` when running from source.

### Recent feature releases

| Version | Highlights |
|---------|------------|
| **v3.27** | Snippet editor: duplicate/move between YAML files · Homebrew tap PR in release CI · native menu bar dialogs |
| **v3.26** | Scheduled auto-backup · sync conflict detection · plugin allowlist · docs (YAML, Troubleshooting, Architecture) |
| **v3.25** | `expando health` · support bundle · E2E secure-input + listener watchdog |
| **v3.24** | `hub upgrade` / `hub outdated` · hub update badge in menu bar · 10 community packages |
| **v3.18–v3.23** | Hub marketplace Pages · doctor full HTML/JSON · Sparkle/notarization CI · snippet editor AppKit |

Community packages: `typing-it`, `meeting-it`, `writing-it`, `devops-it`, `finance-it`, and more — `expando hub list`.  
Hub site: [andreapostiglione.github.io/expando/hub-marketplace.html](https://andreapostiglione.github.io/expando/hub-marketplace.html)

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
| 📟 | **Menu bar native** | Always-visible status, toggle, new snippet, search, edit |
| 🔎 | **Fuzzy search** | `⌘⇧E` → live filter + preview panel |
| 📝 | **Multi-field forms** | Single-window input for dynamic snippets |
| 🎯 | **Advanced app rules** | Filter by app name, bundle ID, or window title |
| 📦 | **Packages** | Organize snippets in reusable bundles |
| 🩺 | **Built-in doctor** | Permissions, repair mode, marketplace sync, crash/safe-mode status |
| 🔄 | **Self-healing** | Listener watchdog, crash-loop backoff, config rollback to last-good |
| 📡 | **Hub marketplace** | Community packages, submit/review workflow, GitHub Pages |
| ✨ | **Native Sparkle updates** | Signed DMG, appcast, helper smoke test in release CI |
| 💾 | **Backup / restore** | One-command config export |
| 🛡️ | **Shell sandbox** | Whitelist allowed shell commands |
| 🐍 | **Hackable** | Plain Python + YAML — extend in minutes |

---

## Quick start

### 1. Install

**DMG (recommended for users):**

1. Download `Expando.dmg` from the [latest GitHub Release](https://github.com/andreapostiglione/expando/releases/latest).
2. Open the DMG and drag `Expando.app` to `/Applications`.
3. Launch `Expando.app`. The menu bar icon appears after macOS permissions are granted.

macOS will require Accessibility and Input Monitoring permissions. That is expected for a text expander because Expando listens for typed triggers and injects the replacement text locally.

**Homebrew cask:**

```bash
brew install --cask andreapostiglione/tap/expando
```

**From source (contributors/development):**

```bash
git clone https://github.com/andreapostiglione/expando.git
cd expando
./install.sh
./scripts/build-macos-app.sh
```

Website: [andreapostiglione.github.io/expando](https://andreapostiglione.github.io/expando/)

### 2. Grant permissions

Open **System Settings → Privacy & Security** and enable:

1. **Accessibility** — `Expando.app` for DMG/Homebrew installs, or the runtime shown by `expando doctor` for source installs
2. **Input Monitoring** — the same app/runtime (required for global key listening)

Verify from the menu bar with **Runtime health**. If you are running from source or have the CLI available:

```bash
expando doctor
expando doctor --repair   # fix stale pid/locks, safe mode, orphan processes
```

### 3. Run

DMG/Homebrew users can open `Expando.app` from `/Applications`.

Source/CLI users:

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
| Menu bar icon | Status, new snippet, search, edit, restart, quit |

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
| `expando doctor` | Full health check (permissions, listener, marketplace) |
| `expando doctor --repair` | Repair stale pid, locks, orphans, safe mode |
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
| `expando hub portal publish-site` | Regenerate Hub Pages HTML + JSON + trigger dashboard + maintainer portal |
| `expando hub portal pending-diff` | Export remote vs local pending metadata diff (JSON) |
| `expando doctor --full-json` | Export full health JSON (doctor, marketplace, histories, validation) |
| `expando doctor --full-html` | Write full health HTML dashboard |
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
brew install --cask andreapostiglione/tap/expando
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
├── tests/                # pytest tests (unit + opt-in macOS E2E)
├── CHANGELOG.md          # Release notes
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
| Snippets don't expand | Open **Runtime health** from the menu bar, or run `expando doctor`; enable **Accessibility** and **Input Monitoring** for `Expando.app` (DMG/Homebrew) or the runtime shown by doctor (source/dev) |
| Worked yesterday, dead today | `expando doctor --repair && expando restart` |
| Menu bar restart broke snippets | Fixed in v3.28 — update and use **Riavvia servizio** (no duplicate listener) |
| `python3.x` in Privacy settings | Normal only when running from source/dev; grant both permissions to that binary |
| Multiple instances / stale lock | `expando stop` · `expando doctor --repair` · `expando start` |
| Config not reloading | `auto_restart: true` in `config/default.yml`; invalid YAML rolls back to `.last-good/` |
| Expando disabled after crashes | Safe mode — `expando doctor --repair` clears it |

```bash
expando doctor              # permissions, listener, marketplace, crash warnings
expando doctor --repair     # stale pid, locks, orphan PIDs, safe mode
expando crashes list        # local crash reports (never uploaded)
expando logs --tail         # follow live log
```

Logs: `~/Library/Application Support/expando/expando.log`  
More: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## Roadmap

Current release: **v3.29.11**. See [ROADMAP.md](ROADMAP.md) for completed sprints and backlog.

## Contributing

Contributions welcome. Fork the repo, create a branch, add tests, open a PR. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

1. `pip install -e ".[dev]"`
2. `pytest -q tests --ignore=tests/e2e`
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
