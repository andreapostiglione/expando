# Expando

Clone open-source di [Espanso](https://espanso.org): text expander system-wide, 100% locale, configurazione YAML compatibile.

## Funzionalità

- Espansione snippet con trigger (`:hello` → testo)
- Variabili dinamiche: `date`, `shell`, `clipboard`
- Trigger multipli e regex
- Toggle on/off con doppio tap su `ALT` (configurabile)
- Auto-reload della config quando modifichi i file YAML
- CLI simile a Espanso: `start`, `stop`, `status`, `path`, `edit`, `doctor`
- Backend `auto` / `inject` / `clipboard` per testi lunghi o multilinea

## Installazione

```bash
cd expando
pip install -e ".[dev]"
```

## Primo avvio

```bash
expando doctor
expando start
```

## Avvio automatico (macOS)

```bash
./scripts/install-launch-agent.sh
```

Installa un LaunchAgent che avvia Expando ad ogni login. Per rimuoverlo:

```bash
./scripts/uninstall-launch-agent.sh
```

La configurazione viene creata in:

- **macOS**: `~/Library/Application Support/expando`
- **Linux**: `~/.config/expando`
- **Windows**: `%AppData%\expando`

## Usare la config di Espanso

Puoi copiare o symlinkare le cartelle `config/` e `match/` dalla tua installazione Espanso:

```bash
cp -R "$HOME/Library/Application Support/espanso/match"/* \
  "$HOME/Library/Application Support/expando/match/"
```

## Esempio snippet

```yaml
matches:
  - trigger: ":email"
    replace: "nome@esempio.it"

  - trigger: ":date"
    replace: "{{mydate}}"
    vars:
      - name: mydate
        type: date
        params:
          format: "%d/%m/%Y"
```

## Permessi macOS

Expando richiede **Accessibilità** e **Input Monitoring** in Impostazioni di sistema → Privacy e sicurezza, per intercettare e iniettare testo come fa Espanso.

## Comandi

| Comando | Descrizione |
|---------|-------------|
| `expando start` | Avvia il daemon in background |
| `expando stop` | Ferma il daemon |
| `expando restart` | Riavvia |
| `expando status` | Stato del processo |
| `expando run` | Foreground (debug) |
| `expando edit` | Apre `match/base.yml` |
| `expando match :date` | Testa un trigger |
| `expando doctor` | Valida la configurazione |

## Limitazioni rispetto a Espanso

- Nessuna search bar, forms UI, package hub, o config per-app
- Nessun supporto immagini
- Wayland/Linux meno testato
- Scritto in Python (più semplice da modificare, leggermente meno performante)

## Licenza

MIT