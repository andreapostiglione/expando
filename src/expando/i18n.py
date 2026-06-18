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
    "notarize.title.ok": {"it": "Audit notarizzazione OK", "en": "Notarization audit OK"},
    "notarize.history.title": {
        "it": "Storico audit notarizzazione",
        "en": "Notarization audit history",
    },
    "notarize.history.path": {"it": "File", "en": "File"},
    "notarize.history.stats": {
        "it": "Esecuzioni: {total} (ok={ok}, fail={failed}) · ultimi 10: {recent_rate} ok",
        "en": "Runs: {total} (ok={ok}, fail={failed}) · last 10: {recent_rate} ok",
    },
    "notarize.history.na": {"it": "n/d", "en": "n/a"},
    "notarize.history.empty": {
        "it": "Nessuna esecuzione registrata — usa expando notarize-audit --record",
        "en": "No recorded runs — use expando notarize-audit --record",
    },
    "notarize.history.recent": {
        "it": "Ultime {limit} esecuzioni:",
        "en": "Last {limit} runs:",
    },
    "notarize.history.ok": {"it": "OK", "en": "OK"},
    "notarize.history.fail": {"it": "FAIL", "en": "FAIL"},
    "notarize.history.entry": {
        "it": "  {recorded_at}  {status}  pass={pass_count} warn={warn_count} fail={fail_count}",
        "en": "  {recorded_at}  {status}  pass={pass_count} warn={warn_count} fail={fail_count}",
    },
    "notarize.history.recorded": {
        "it": "Registrato in {path} ({recorded_at})",
        "en": "Recorded in {path} ({recorded_at})",
    },
    "notarize.title.issues": {
        "it": "PROBLEMI NOTARIZZAZIONE",
        "en": "NOTARIZATION ISSUES",
    },
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
    "cli.hub.installed_marker": {"it": " [installato]", "en": " [installed]"},
    "cli.hub.publish.ok": {
        "it": "Package {package_id} valido ({matches} snippet).",
        "en": "Package {package_id} is valid ({matches} snippet(s)).",
    },
    "cli.hub.publish.installed": {
        "it": "Installato in {path}",
        "en": "Installed to {path}",
    },
    "cli.hub.publish.bundled": {
        "it": "Copiato nel bundle in {path}",
        "en": "Bundled to {path}",
    },
    "cli.hub.publish.registered": {
        "it": "Registrato in packages/hub/index.json",
        "en": "Registered in packages/hub/index.json",
    },
    "cli.hub.publish.error": {"it": "Validazione fallita:", "en": "Validation failed:"},
    "cli.hub.publish.warning": {"it": "Avvisi:", "en": "Warnings:"},
    "benchmark.matches": {"it": "Snippet", "en": "Matches"},
    "benchmark.compile": {"it": "Compilazione", "en": "Compile"},
    "benchmark.reload": {"it": "Ricarica", "en": "Reload"},
    "benchmark.handle_char": {
        "it": "handle_char (nessun match)",
        "en": "handle_char (no match)",
    },
    "benchmark.handle_char_latency": {
        "it": "Latenza handle_char",
        "en": "handle_char latency",
    },
    "benchmark.expand_lookup": {"it": "Lookup espansione", "en": "expand lookup"},
    "benchmark.ops_per_sec": {"it": "ops/s su", "en": "ops/s over"},
    "benchmark.iterations": {"it": "iterazioni", "en": "iterations"},
    "cli.packages.none": {"it": "Nessun pacchetto installato.", "en": "No packages installed."},
    "cli.restored": {"it": "Configurazione ripristinata.", "en": "Configuration restored."},
    "cli.plugins.none": {"it": "Nessun plugin caricato.", "en": "No plugins loaded."},
    "cli.export.written": {"it": "Snippet esportato in {path}", "en": "Snippet exported to {path}"},
    "cli.duplicate.done": {
        "it": "Duplicato {source} → {target} in {path}",
        "en": "Duplicated {source} → {target} in {path}",
    },
    "stats.config": {"it": "Config track_expansions", "en": "Config track_expansions"},
    "stats.recording": {"it": "Registrazione attiva", "en": "Recording enabled"},
    "stats.total": {"it": "Espansioni totali", "en": "Total expansions"},
    "stats.updated": {"it": "Ultimo aggiornamento", "en": "Last updated"},
    "stats.by_trigger": {"it": "Per trigger:", "en": "By trigger:"},
    "stats.enabled": {"it": "Statistiche locali attivate.", "en": "Local stats recording enabled."},
    "stats.disabled": {"it": "Statistiche locali disattivate.", "en": "Local stats recording disabled."},
    "stats.need_config": {
        "it": "Imposta track_expansions: true in config/default.yml per abilitare il conteggio.",
        "en": "Set track_expansions: true in config/default.yml to allow counting.",
    },
    "registry.title": {"it": "Registry Expando", "en": "Expando registry"},
    "registry.index": {"it": "Hub index", "en": "Hub index"},
    "registry.hub_packages": {"it": "Hub packages:", "en": "Hub packages:"},
    "registry.installed_packages": {"it": "Package installati:", "en": "Installed packages:"},
    "registry.plugins": {"it": "Plugin:", "en": "Plugins:"},
    "sync.config_dir": {"it": "Cartella config", "en": "Config directory"},
    "sync.resolved": {"it": "Percorso reale", "en": "Resolved path"},
    "sync.mode": {"it": "Modalità", "en": "Mode"},
    "sync.symlink_target": {"it": "Target symlink", "en": "Symlink target"},
    "sync.git": {"it": "Git", "en": "Git"},
    "sync.git_none": {"it": "non inizializzato", "en": "not initialized"},
    "sync.git_clean": {"it": "repo pulito", "en": "clean repo"},
    "sync.git_dirty": {"it": "modifiche non committate", "en": "uncommitted changes"},
    "sync.paths_hint": {"it": "Cartelle consigliate per sync:", "en": "Recommended sync paths:"},
    "sync.git_missing": {"it": "git non trovato nel PATH", "en": "git not found in PATH"},
    "sync.git_initialized": {"it": "Repository git inizializzato.", "en": "Git repository initialized."},
    "sync.gitignore_written": {"it": ".gitignore aggiornato.", "en": ".gitignore updated."},
    "sync.git_committed": {"it": "Commit iniziale creato.", "en": "Initial commit created."},
    "sync.git_commit_skipped": {"it": "Nessuna modifica da committare.", "en": "Nothing to commit."},
    "sync.git_next_steps": {
        "it": "Aggiungi un remote privato e fai push di config/, match/, plugins/.",
        "en": "Add a private remote and push config/, match/, plugins/.",
    },
    "sync.icloud_macos_only": {
        "it": "Sync iCloud disponibile solo su macOS.",
        "en": "iCloud sync is only available on macOS.",
    },
    "sync.icloud_unavailable": {
        "it": "iCloud Drive non trovato su questo Mac.",
        "en": "iCloud Drive was not found on this Mac.",
    },
    "sync.already_linked": {"it": "Config già collegata:", "en": "Config already linked:"},
    "sync.backup_created": {"it": "Backup locale: {path}", "en": "Local backup: {path}"},
    "sync.backup_exists": {
        "it": "Esiste già un backup pre-icloud; rimuovilo prima di riprovare.",
        "en": "A pre-iCloud backup already exists; remove it before retrying.",
    },
    "sync.would_backup": {"it": "Backup previsto: {path}", "en": "Would backup to: {path}"},
    "sync.dry_run": {"it": "Dry-run — nessuna modifica:", "en": "Dry-run — no changes:"},
    "sync.icloud_linked": {"it": "Config collegata a iCloud:", "en": "Config linked to iCloud:"},
    "sync.icloud_hint": {
        "it": "Modifica snippet da un solo Mac alla volta per evitare conflitti YAML.",
        "en": "Edit snippets from one Mac at a time to avoid YAML merge conflicts.",
    },
    "hub.submit.ok": {
        "it": "Package {package_id} valido ({matches} snippet).",
        "en": "Package {package_id} is valid ({matches} snippet(s)).",
    },
    "hub.submit.bundle": {"it": "Bundle invio: {path}", "en": "Submission bundle: {path}"},
    "hub.submit.steps": {"it": "Prossimi passi:", "en": "Next steps:"},
    "hub.submit.step_issue": {
        "it": "Apri una issue «Hub package» su GitHub",
        "en": "Open a Hub package issue on GitHub",
    },
    "hub.submit.step_attach": {
        "it": "Allega lo zip e descrivi il package",
        "en": "Attach the zip and describe the package",
    },
    "hub.submit.step_docs": {"it": "Leggi la guida marketplace", "en": "Read the marketplace guide"},
    "hub.submit.maintainer": {
        "it": "Per maintainer del repo ufficiale:",
        "en": "For official repo maintainers:",
    },
    "hub.submit.review_hint": {
        "it": "Flusso review locale (maintainer):",
        "en": "Local review flow (maintainers):",
    },
    "hub.review.empty": {
        "it": "Nessun package con stato {status}.",
        "en": "No packages with status {status}.",
    },
    "hub.review.header": {
        "it": "Marketplace ({status}, {count}):",
        "en": "Marketplace ({status}, {count}):",
    },
    "hub.review.submitted": {"it": "Inviato", "en": "Submitted"},
    "hub.review.reviewed": {"it": "Revisionato", "en": "Reviewed"},
    "hub.review.reviewer": {"it": "Reviewer", "en": "Reviewer"},
    "hub.review.note": {"it": "Nota", "en": "Note"},
    "hub.review.queued": {
        "it": "Package {package_id} aggiunto alla coda pending.",
        "en": "Package {package_id} queued as pending.",
    },
    "hub.review.approved": {
        "it": "Package {package_id} approvato.",
        "en": "Package {package_id} approved.",
    },
    "hub.review.rejected": {
        "it": "Package {package_id} rifiutato.",
        "en": "Package {package_id} rejected.",
    },
    "hub.portal.title": {"it": "Hub marketplace portal", "en": "Hub marketplace portal"},
    "hub.portal.local": {"it": "Indice locale", "en": "Local index"},
    "hub.portal.remote": {"it": "Indice remoto", "en": "Remote index"},
    "hub.portal.remote_none": {"it": "non configurato", "en": "not configured"},
    "hub.portal.remote_approved": {
        "it": "Package approvati remoti: {count}",
        "en": "Remote approved packages: {count}",
    },
    "hub.portal.counts": {
        "it": "Coda locale: pending={pending}, approved={approved}, rejected={rejected}, totale={total}",
        "en": "Local queue: pending={pending}, approved={approved}, rejected={rejected}, total={total}",
    },
    "hub.portal.exported": {
        "it": "Indice pubblicabile scritto in {path}",
        "en": "Publishable index written to {path}",
    },
    "hub.portal.synced": {"it": "Sync completata", "en": "Sync completed"},
    "hub.portal.dry_run": {"it": "Dry-run", "en": "Dry-run"},
    "hub.portal.sync_stats": {
        "it": "aggiunti={added}, aggiornati={updated}, invariati={unchanged}",
        "en": "added={added}, updated={updated}, unchanged={unchanged}",
    },
    "hub.portal.published": {
        "it": "Sito marketplace pubblicato: {html} · JSON: {json} · package approvati: {count}",
        "en": "Marketplace site published: {html} · JSON: {json} · approved packages: {count}",
    },
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