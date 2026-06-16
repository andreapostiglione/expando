# Expando

Text expander system-wide per macOS. 100% locale, open source, configurazione YAML.

Scrivi un trigger → ottieni il testo che vuoi. Ovunque.

## Perché Expando

| Pro | Cosa significa per te |
|-----|----------------------|
| **Zero cloud** | I tuoi snippet restano sul Mac. Nessun account, nessun sync remoto |
| **Menu bar nativa** | Stato visibile, attiva/disattiva, cerca snippet, modifica e riavvio |
| **Search bar** | `CMD+SHIFT+E` o menu bar → picker visuale di tutti gli snippet |
| **Forms** | Popup nativi macOS per snippet con campi variabili |
| **Profili per app** | Config diversa in Terminal, browser, ecc. |
| **Packages** | Snippet organizzati in `match/packages/` |
| **Doctor integrato** | Health check di permessi, processi e config |
| **Backup/restore** | Esporta e ripristina la config con un comando |
| **Shell sandbox** | Whitelist comandi permessi nelle variabili shell |
| **Hackable** | Python aperto, leggibile, estendibile |

## Installazione

```bash
git clone https://github.com/andreapostiglione/expando.git
cd expando
./install.sh
./scripts/build-macos-app.sh
```

### Homebrew (tap personale)

```bash
brew install andreapostiglione/tap/expando
```

## Primo avvio

```bash
expando doctor
./scripts/install-launch-agent.sh
```

Concedi **Accessibilità** a `Expando.app` in Impostazioni → Privacy.

## Comandi

| Comando | Descrizione |
|---------|-------------|
| `expando start` / `stop` / `restart` | Gestione daemon |
| `expando status` | Stato processo |
| `expando list` | Elenco snippet |
| `expando add :trigger "testo"` | Aggiunge snippet |
| `expando import ./dir` | Importa YAML |
| `expando search` | Apre il picker snippet |
| `expando match :date` | Testa un trigger |
| `expando doctor` | Health check |
| `expando packages` | Lista package installati |
| `expando backup` | Backup config `.tar.gz` |
| `expando restore file.tar.gz` | Ripristina config |

## Scorciatoie

- **Doppio ALT** — attiva/disattiva Expando
- **CMD+SHIFT+E** — search bar snippet (configurabile)

## Esempio snippet

```yaml
matches:
  - trigger: ":claude"
    replace: "claude --dangerously-skip-permissions"
    if_app: [Terminal, iTerm2, Cursor]

  - trigger: ":sig"
    form:
      - name: name
        label: "Il tuo nome"
    replace: "Cordiali saluti,\n{{name}}"

  - trigger: ":branch"
    replace: "{{output}}"
    vars:
      - name: output
        type: shell
        params:
          cmd: "git branch --show-current"
```

## Profili per app

Crea `config/terminal.yml`:

```yaml
filter:
  app_names:
    - Terminal
    - iTerm2
shell_allowlist:
  - echo
  - git
```

## Packages

Metti snippet in `match/packages/<nome>/`. Expando li carica automaticamente.

## Distribuzione

```bash
./scripts/build-dmg.sh   # crea Expando.dmg
```

## Licenza

MIT