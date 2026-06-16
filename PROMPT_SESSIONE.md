# Prompt per nuova sessione — Miglioramento Expando

Copia tutto il blocco qui sotto in una sessione nuova.

---

## PROMPT (copia da qui)

Sto lavorando su **Expando**, un text expander open-source compatibile con Espanso, sviluppato per Inochi SRL.

### Contesto progetto

- **Repo GitHub:** https://github.com/inochisrl/expando
- **Path locale:** `~/expando` (`/Users/andreapostiglione/expando`)
- **Config utente:** `~/Library/Application Support/expando/`
- **Stack:** Python 3.14, pynput, PyYAML, watchdog, click
- **Avvio automatico:** LaunchAgent `com.inochisrl.expando` in `~/Library/LaunchAgents/`
- **Snippet attivi:** `:claude`, `:ultraclaude`, `:grok`, `:date`, `:shell`, `:espanso` (migrati da Espanso)

Expando funziona già system-wide su macOS. L'utente lo usa principalmente per shortcut CLI nel Terminale.

### Stato attuale (cosa c'è già)

- Engine espansione con buffer keystroke, trigger letterali e regex base
- Variabili dinamiche: `date`, `shell`, `clipboard`
- CLI: `start`, `stop`, `restart`, `status`, `run`, `path`, `edit`, `doctor`, `match`
- Injector con backend `auto` / `inject` / `clipboard`
- Auto-reload config YAML via watchdog
- Toggle on/off con doppio tap ALT
- LaunchAgent per avvio al login
- Test base su config e renderer (4 test pytest)

### Problemi noti da risolvere

1. Permessi macOS legati a `python3.14` invece di un'app dedicata
2. Possibili istanze duplicate (LaunchAgent + `expando start` manuale)
3. `doctor` non verifica permessi né conflitti di processo
4. Nessun feedback visivo quando si fa toggle ON/OFF
5. Nessuna icona menu bar
6. Test suite insufficiente, nessuna CI

### Piano di miglioramento (4 fasi)

**Fase 1 — Stabilità e UX macOS (INIZIA DA QUI)**
- 1.1 App `.app` nativa (PyInstaller o py2app) → permessi Privacy puliti
- 1.2 Single-instance lock → zero daemon duplicati
- 1.3 `expando doctor` avanzato → permessi, processi, YAML, trigger duplicati
- 1.4 Notifica macOS al toggle ON/OFF
- 1.5 Menu bar (rumps) con stato + Disable/Edit/Restart/Quit
- 1.6 Log strutturati con rotazione

**Fase 2 — Produttività**
- `expando list`, `expando import espanso`, `expando add`
- Regole per-app (`if_app: Terminal`) e blacklist app
- Variabile `env` (`{{USER}}`, `{{HOME}}`, `{{cwd}}`)
- Snippet Inochi in `match/inochi.yml`

**Fase 3 — Parità Espanso (solo se serve)**
- Forms semplici (dialog nativo macOS)
- Search bar
- Regex avanzati, profili config, package manager minimale

**Fase 4 — Distribuzione**
- CI GitHub Actions, Homebrew tap `inochisrl/tap`, release `.dmg` firmata, sync config via Git

### Istruzioni per questa sessione

1. Leggi il codice in `~/expando/src/expando/` prima di modificare
2. Implementa la **Fase 1 completa** (1.1 → 1.6), in ordine di dipendenza
3. Non fare refactor non necessari — cambiamenti focalizzati
4. Aggiungi test per ogni feature nuova
5. Aggiorna README con le nuove funzionalità
6. Verifica che funzioni su macOS (permessi, LaunchAgent, toggle, espansione `:claude`)
7. Committa su branch `feat/fase-1-stabilita` e apri PR su `inochisrl/expando`

### Vincoli

- Resta compatibile con il formato YAML Espanso esistente
- Non inviare dati in rete — tutto locale
- Non rompere il LaunchAgent già installato
- Segui lo stile del codice esistente (dataclass, click CLI, pathlib)
- Esegui i comandi tu stesso, non dire all'utente cosa fare

### Definition of done Fase 1

- [ ] Una sola istanza Expando può girare
- [ ] `expando doctor` riporta permessi, stato processo, errori config
- [ ] Toggle mostra notifica "Expando enabled/disabled"
- [ ] Icona menu bar con menu funzionante
- [ ] Log in `~/Library/Application Support/expando/expando.log`
- [ ] App `.app` o binario dedicato per permessi macOS (non solo python3.14)
- [ ] Test pytest passano
- [ ] README aggiornato

Inizia esplorando il repo, poi implementa Fase 1.

## FINE PROMPT