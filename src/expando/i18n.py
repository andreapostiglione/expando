from __future__ import annotations

import os

_LOCALE = os.environ.get("EXPANDO_LOCALE", "it").lower()

_STRINGS: dict[str, dict[str, str]] = {
    "doctor.title.ok": {"it": "OK", "en": "OK"},
    "doctor.title.issues": {"it": "PROBLEMI RILEVATI", "en": "ISSUES FOUND"},
    "doctor.config_dir": {"it": "Cartella config", "en": "Config dir"},
    "doctor.daemon_running": {"it": "Daemon attivo", "en": "Daemon running"},
    "doctor.pid": {"it": "PID", "en": "PID"},
    "doctor.processes": {"it": "Processi Expando", "en": "Expando processes"},
    "doctor.matches": {"it": "Snippet caricati", "en": "Matches loaded"},
    "doctor.accessibility": {"it": "Accessibilità", "en": "Accessibility"},
    "doctor.input_monitoring": {"it": "Monitoraggio input", "en": "Input monitoring"},
    "doctor.injection": {"it": "Injection tastiera", "en": "Keyboard injection"},
    "doctor.runtime": {"it": "Modalità esecuzione", "en": "Runtime mode"},
    "doctor.grant_target": {"it": "Abilita in Impostazioni", "en": "Enable in Settings"},
    "doctor.perm.granted": {"it": "concesso", "en": "granted"},
    "doctor.perm.missing": {"it": "mancante", "en": "missing"},
    "doctor.perm.unknown": {"it": "sconosciuto", "en": "unknown"},
    "doctor.config_errors": {"it": "Errori config", "en": "Config errors"},
    "doctor.duplicates": {"it": "Trigger duplicati", "en": "Duplicate triggers"},
    "doctor.warnings": {"it": "Avvisi", "en": "Warnings"},
    "doctor.yes": {"it": "sì", "en": "yes"},
    "doctor.no": {"it": "no", "en": "no"},
    "wizard.title": {"it": "Configura Expando", "en": "Set up Expando"},
    "wizard.welcome": {
        "it": "Expando espande i tuoi snippet in tutte le app. Serve autorizzare macOS per leggere e scrivere testo.",
        "en": "Expando expands snippets system-wide. macOS must allow keyboard access for listen and inject.",
    },
    "wizard.accessibility.title": {"it": "Passo 1 — Accessibilità", "en": "Step 1 — Accessibility"},
    "wizard.accessibility.body": {
        "it": "Serve per cancellare il trigger e incollare il testo espanso. Abilita il programma indicato sotto.",
        "en": "Required to delete triggers and paste expanded text. Enable the program shown below.",
    },
    "wizard.input.title": {"it": "Passo 2 — Monitoraggio input", "en": "Step 2 — Input Monitoring"},
    "wizard.input.body": {
        "it": "Serve per intercettare i tasti mentre digiti. Consigliato su macOS recenti.",
        "en": "Required to listen for keystrokes while typing. Recommended on recent macOS.",
    },
    "wizard.done": {
        "it": "Setup completato. Se qualcosa non espande, esegui `expando doctor`.",
        "en": "Setup complete. If expansion fails, run `expando doctor`.",
    },
    "wizard.open_settings": {"it": "Apri Impostazioni", "en": "Open Settings"},
    "wizard.recheck": {"it": "Verifica di nuovo", "en": "Check again"},
    "wizard.continue": {"it": "Continua", "en": "Continue"},
    "wizard.skip": {"it": "Salta", "en": "Skip"},
    "wizard.finish": {"it": "Fine", "en": "Finish"},
    "runtime.app": {"it": "app bundle", "en": "app bundle"},
    "runtime.dev": {"it": "sviluppo (Python)", "en": "development (Python)"},
    "runtime.venv": {"it": "venv locale", "en": "local venv"},
    "runtime.unknown": {"it": "sconosciuta", "en": "unknown"},
    "notify.block.title": {"it": "Expando", "en": "Expando"},
    "notify.block.secure_input": {
        "it": "Espansione bloccata: campo password attivo (secure input).",
        "en": "Expansion blocked: secure input is active (password field).",
    },
    "notify.block.secure_input_trigger": {
        "it": "Espansione di {trigger} bloccata: campo password attivo.",
        "en": "Expansion of {trigger} blocked: secure input is active.",
    },
    "notify.block.app_rule": {
        "it": "{trigger} non disponibile in {app}.",
        "en": "{trigger} is not available in {app}.",
    },
    "notify.block.app_rule_detail": {
        "it": "{trigger} non disponibile in {app} ({detail}).",
        "en": "{trigger} is not available in {app} ({detail}).",
    },
    "notify.block.shell_denied": {
        "it": "{trigger} usa un comando shell non consentito.",
        "en": "{trigger} uses a shell command that is not allowed.",
    },
    "notify.block.unknown_app": {"it": "questa app", "en": "this app"},
    "update.title": {"it": "Expando", "en": "Expando"},
    "update.available": {
        "it": "Disponibile la versione {version}. Scarica da GitHub Releases.",
        "en": "Version {version} is available. Download from GitHub Releases.",
    },
    "changelog.title": {"it": "Expando aggiornato", "en": "Expando updated"},
    "changelog.new_version": {
        "it": "Benvenuto in Expando {version}. Vedi le novità su GitHub.",
        "en": "Welcome to Expando {version}. See what's new on GitHub.",
    },
    "cli.status.running": {"it": "expando è attivo (pid {pid})", "en": "expando is running (pid {pid})"},
    "cli.status.stopped": {"it": "expando non è attivo", "en": "expando is not running"},
    "cli.started": {"it": "expando avviato (pid {pid})", "en": "expando started (pid {pid})"},
    "cli.stopped": {"it": "expando fermato", "en": "expando stopped"},
    "cli.not_running": {"it": "expando non era attivo", "en": "expando was not running"},
    "cli.restarted": {"it": "expando riavviato (pid {pid})", "en": "expando restarted (pid {pid})"},
    "cli.added": {
        "it": "Aggiunto {trigger} in {path}",
        "en": "Added {trigger} to {path}",
    },
    "cli.created": {
        "it": "Creato {trigger} da template '{template}' in {path}",
        "en": "Created {trigger} from template '{template}' in {path}",
    },
    "cli.templates.header": {"it": "Template disponibili:", "en": "Available templates:"},
    "cli.no_crashes": {
        "it": "Nessun crash report in {path}",
        "en": "No crash reports in {path}",
    },
    "security.title.ok": {"it": "OK", "en": "OK"},
    "security.title.issues": {"it": "PROBLEMI RILEVATI", "en": "ISSUES FOUND"},
    "menubar.disable": {"it": "Disattiva", "en": "Disable"},
    "menubar.enable": {"it": "Attiva", "en": "Enable"},
    "menubar.search": {"it": "Cerca snippet", "en": "Search snippets"},
    "menubar.hub": {"it": "Package hub", "en": "Package hub"},
    "menubar.editor": {"it": "Editor snippet", "en": "Snippet editor"},
    "menubar.restart": {"it": "Riavvia", "en": "Restart"},
    "menubar.updates": {"it": "Controlla aggiornamenti", "en": "Check for updates"},
    "menubar.quit": {"it": "Esci", "en": "Quit"},
    "menubar.installed": {
        "it": "Pacchetto {package} installato",
        "en": "Installed package {package}",
    },
    "menubar.install_failed": {
        "it": "Installazione pacchetto fallita: {error}",
        "en": "Package install failed: {error}",
    },
    "menubar.restarted": {"it": "Servizio riavviato", "en": "Service restarted"},
    "menubar.up_to_date": {
        "it": "Expando è aggiornato.",
        "en": "Expando is up to date.",
    },
    "menubar.update_failed": {
        "it": "Controllo aggiornamenti fallito: {error}",
        "en": "Update check failed: {error}",
    },
    "doctor.crash_warning": {
        "it": "{count} crash report negli ultimi 7 giorni — esegui `expando crashes`.",
        "en": "{count} crash report(s) in the last 7 days — run `expando crashes`.",
    },
    "cli.import.header": {"it": "Importati:", "en": "Imported:"},
    "cli.import.item": {"it": "  - {name}", "en": "  - {name}"},
    "cli.backup_created": {"it": "Backup creato: {path}", "en": "Backup created: {path}"},
    "cli.imported_from": {"it": "Importato da {source}", "en": "Imported from {source}"},
    "cli.config_merged": {"it": "  - config/default.yml unito", "en": "  - merged config/default.yml"},
    "cli.matches_imported": {
        "it": "  - {count} match in {files} file",
        "en": "  - {count} matches in {files} file(s)",
    },
    "cli.matches_skipped": {
        "it": "  - saltati {count} match non supportati",
        "en": "  - skipped {count} unsupported match(es)",
    },
    "cli.snippets_skipped": {
        "it": "  - saltati {count} snippet non supportati",
        "en": "  - skipped {count} unsupported snippet(s)",
    },
    "cli.wrote_file": {"it": "  - scritto {name}", "en": "  - wrote {name}"},
    "cli.warning": {"it": "  ! {message}", "en": "  ! {message}"},
    "cli.hub.installed": {"it": "Installato {package} in {path}", "en": "Installed {package} to {path}"},
    "cli.hub.removed": {"it": "Rimosso pacchetto {package}", "en": "Removed package {package}"},
    "cli.hub.not_installed": {
        "it": "Pacchetto non installato: {package}",
        "en": "Package not installed: {package}",
    },
    "cli.hub.already_installed": {"it": "Pacchetto già installato.", "en": "Package already installed."},
    "cli.hub.no_selection": {"it": "Nessun pacchetto selezionato", "en": "No package selected"},
    "cli.packages.none": {"it": "Nessun pacchetto installato.", "en": "No packages installed."},
    "cli.restored": {"it": "Configurazione ripristinata.", "en": "Configuration restored."},
    "cli.plugins.none": {"it": "Nessun plugin caricato.", "en": "No plugins loaded."},
    "cli.update.available": {
        "it": "Aggiornamento disponibile: v{version}",
        "en": "Update available: v{version}",
    },
    "cli.update.current": {
        "it": "Expando v{version} è aggiornato.",
        "en": "Expando v{version} is up to date.",
    },
    "cli.update.failed": {
        "it": "Controllo aggiornamenti fallito: {error}",
        "en": "Update check failed: {error}",
    },
    "cli.trigger_not_found": {
        "it": "Trigger non trovato: {trigger}",
        "en": "Trigger not found: {trigger}",
    },
    "cli.render_cancelled": {
        "it": "Rendering snippet annullato",
        "en": "Snippet rendering cancelled",
    },
    "cli.match.app": {"it": "App: {app}", "en": "App: {app}"},
    "cli.match.allowed_yes": {"it": "Consentito: sì", "en": "Allowed: yes"},
    "cli.match.allowed_no": {"it": "Consentito: no", "en": "Allowed: no"},
    "cli.crash.not_found": {
        "it": "Crash report non trovato: {name}",
        "en": "Crash report not found: {name}",
    },
    "cli.crash.none": {"it": "Nessun crash report trovato", "en": "No crash reports found"},
}


def t(key: str, *, locale: str | None = None) -> str:
    lang = (locale or _LOCALE).lower()
    entry = _STRINGS.get(key, {})
    if lang in entry:
        return entry[lang]
    if "en" in entry:
        return entry["en"]
    return key


def tf(key: str, *, locale: str | None = None, **kwargs: object) -> str:
    return t(key, locale=locale).format(**kwargs)