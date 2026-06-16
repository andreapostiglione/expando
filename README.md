# Expando

Text expander system-wide per macOS. 100% locale, open source, configurazione YAML.

Scrivi un trigger → ottieni il testo che vuoi. Ovunque.

## Perché Expando

| Pro | Cosa significa per te |
|-----|----------------------|
| **Zero cloud** | I tuoi snippet restano sul Mac. Nessun account, nessun sync remoto, nessun tracking |
| **Menu bar nativa** | Stato sempre visibile, attiva/disattiva, modifica e riavvio in un click |
| **Doctor integrato** | `expando doctor` controlla permessi, processi, config e trigger duplicati |
| **Avvio al login** | LaunchAgent incluso, parte da solo dopo il reboot |
| **Notifiche toggle** | Doppio ALT e sai subito se è attivo o meno |
| **Single-instance** | Un solo daemon, zero conflitti tra istanze |
| **YAML semplice** | Config leggibile, versionabile con Git, modificabile a mano |
| **Hackable** | Python aperto: aggiungi logiche, integrazioni e variabili custom in minuti |
| **Leggero** | Nessun motore pesante, nessuna UI complessa da imparare |

## Funzionalità

- Espansione snippet con trigger (`:hello` → testo)
- Variabili dinamiche: `date`, `shell`, `clipboard`
- Trigger multipli e regex
- Toggle on/off con doppio tap su `ALT` (configurabile) + notifica macOS
- Menu bar con stato, attiva/disattiva, modifica snippet, riavvio
- Log rotanti in `~/Library/Application Support/expando/expando.log`
- Auto-reload della config quando modifichi i file YAML
- CLI: `start`, `stop`, `status`, `path`, `edit`, `doctor`, `match`
- Backend `auto` / `inject` / `clipboard` per testi lunghi o multilinea
- `Expando.app` per permessi Privacy macOS puliti

## Installazione

```bash
git clone https://github.com/andreapostiglione/expando.git
cd expando
./install.sh
```

## Primo avvio

```bash
./scripts/build-macos-app.sh
expando doctor
expando start
```

## Avvio automatico (macOS)

```bash
./scripts/install-launch-agent.sh
```

Per rimuoverlo:

```bash
./scripts/uninstall-launch-agent.sh
```

La configurazione vive in `~/Library/Application Support/expando/`.

## Esempio snippet

```yaml
matches:
  - trigger: ":email"
    replace: "nome@esempio.it"

  - trigger: ":claude"
    replace: "claude --dangerously-skip-permissions"
    if_app:
      - Terminal
      - iTerm2
      - Cursor

  - trigger: ":date"
    replace: "{{mydate}}"
    vars:
      - name: mydate
        type: date
        params:
          format: "%d/%m/%Y"

  - trigger: ":whoami"
    replace: "{{USER}} @ {{cwd}}"

  - trigger: ":deploy"
    replace: "{{output}}"
    vars:
      - name: output
        type: shell
        params:
          cmd: "git branch --show-current"
```

### Regole per app

- `if_app` — snippet attivo solo in quelle app
- `unless_app` — snippet disattivato in quelle app
- `app_blacklist` in `config/default.yml` — disattiva Expando del tutto in certe app

## Permessi macOS

Expando richiede **Accessibilità** in Impostazioni → Privacy e sicurezza. Dopo `build-macos-app.sh`, abilita **Expando.app**.

```bash
expando doctor
```

## Comandi

| Comando | Descrizione |
|---------|-------------|
| `expando start` | Avvia il daemon |
| `expando stop` | Ferma il daemon |
| `expando restart` | Riavvia |
| `expando status` | Stato del processo |
| `expando run` | Foreground (debug) |
| `expando edit` | Apre `match/base.yml` |
| `expando match :date` | Testa un trigger |
| `expando doctor` | Health check completo |
| `expando list` | Elenco snippet configurati |
| `expando add :trigger "testo"` | Aggiunge uno snippet da CLI |
| `expando import ./cartella` | Importa file YAML di snippet |

## Filosofia

Expando punta alla semplicità radicale: pochi file, codice leggibile, nessuna dipendenza da servizi esterni. Pensato per chi vuole uno strumento personale, trasparente e sotto controllo totale.

## Licenza

MIT — vedi [LICENSE](LICENSE).