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
    "wizard.open_permissions": {
        "it": "Apri permessi",
        "en": "Open permissions",
    },
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
    "notarize.history.svg_written": {
        "it": "Grafico trend notarization scritto in {path}",
        "en": "Notarization trend SVG written to {path}",
    },
    "notarize.history.exported": {
        "it": "Storico audit esportato in {path}",
        "en": "Audit history exported to {path}",
    },
    "notarize.title.issues": {
        "it": "PROBLEMI NOTARIZZAZIONE",
        "en": "NOTARIZATION ISSUES",
    },
    "menubar.title_enabled": {"it": "Expando ●", "en": "Expando ●"},
    "menubar.title_disabled": {"it": "Expando ○", "en": "Expando ○"},
    "menubar.title_listener_dead": {"it": "Expando ⚠", "en": "Expando ⚠"},
    "menubar.listener_dead": {
        "it": "Listener tastiera non attivo — riavvio automatico in corso",
        "en": "Keyboard listener is down — auto-restart in progress",
    },
    "menubar.disable": {"it": "Disattiva", "en": "Disable"},
    "menubar.enable": {"it": "Attiva", "en": "Enable"},
    "menubar.search": {"it": "Cerca snippet", "en": "Search snippets"},
    "menubar.new_snippet": {"it": "Nuovo snippet", "en": "New snippet"},
    "ui.cancel": {"it": "Annulla", "en": "Cancel"},
    "ui.confirm": {"it": "Conferma", "en": "Confirm"},
    "ui.ok": {"it": "OK", "en": "OK"},
    "ui.form.title": {
        "it": "Compila i campi dello snippet",
        "en": "Fill in the snippet fields",
    },
    "ui.insert": {"it": "Inserisci", "en": "Insert"},
    "menubar.restore_picker": {
        "it": "Scegli backup da ripristinare",
        "en": "Choose a backup to restore",
    },
    "menubar.hub": {"it": "Libreria snippet", "en": "Snippet library"},
    "menubar.editor": {"it": "Gestisci snippet", "en": "Manage snippets"},
    "menubar.restart": {"it": "Riavvia Expando", "en": "Restart Expando"},
    "menubar.backup": {"it": "Crea backup", "en": "Create backup"},
    "menubar.restore": {"it": "Ripristina backup", "en": "Restore backup"},
    "menubar.advanced": {"it": "Avanzate", "en": "Advanced"},
    "menubar.backup_created": {
        "it": "Backup creato: {path}",
        "en": "Backup created: {path}",
    },
    "menubar.backup_saved": {
        "it": "Backup salvato ({label}).",
        "en": "Backup saved ({label}).",
    },
    "menubar.backup_failed": {
        "it": "Backup fallito: {error}",
        "en": "Backup failed: {error}",
    },
    "menubar.no_backups": {
        "it": "Nessun backup trovato.",
        "en": "No backups found.",
    },
    "menubar.restored": {
        "it": "Configurazione ripristinata da {path}",
        "en": "Configuration restored from {path}",
    },
    "menubar.restore_confirm_title": {
        "it": "Ripristinare il backup?",
        "en": "Restore this backup?",
    },
    "menubar.restore_confirm_body": {
        "it": "Verrà ripristinato il backup del {label}. La configurazione attuale verrà sostituita.",
        "en": "The backup from {label} will be restored. Your current configuration will be replaced.",
    },
    "menubar.restored_ok": {
        "it": "Configurazione ripristinata dal backup del {label}.",
        "en": "Configuration restored from the {label} backup.",
    },
    "menubar.restore_invalid_rolled_back": {
        "it": "Il backup contiene errori. La configurazione precedente è stata ripristinata.",
        "en": "The backup contains errors. Your previous working configuration was restored.",
    },
    "editor.duplicate.button": {"it": "Duplica", "en": "Duplicate"},
    "editor.duplicate.title": {"it": "Duplica snippet", "en": "Duplicate snippet"},
    "editor.duplicate.body": {
        "it": "Scegli il file YAML di destinazione.",
        "en": "Choose the destination YAML file.",
    },
    "editor.duplicate.select": {
        "it": "Seleziona uno snippet da duplicare.",
        "en": "Select a snippet to duplicate.",
    },
    "editor.duplicate.readonly": {
        "it": "I package hub non possono essere duplicati da qui.",
        "en": "Hub packages cannot be duplicated from here.",
    },
    "editor.move.button": {"it": "Sposta", "en": "Move"},
    "editor.move.title": {"it": "Sposta snippet", "en": "Move snippet"},
    "editor.move.body": {
        "it": "Scegli il file YAML di destinazione.",
        "en": "Choose the destination YAML file.",
    },
    "editor.move.select": {
        "it": "Seleziona uno snippet da spostare.",
        "en": "Select a snippet to move.",
    },
    "editor.move.readonly": {
        "it": "I package hub non possono essere spostati da qui.",
        "en": "Hub packages cannot be moved from here.",
    },
    "editor.move.no_targets": {
        "it": "Non ci sono altri file YAML disponibili.",
        "en": "There are no other YAML files available.",
    },
    "menubar.restore_failed": {
        "it": "Ripristino fallito: {error}",
        "en": "Restore failed: {error}",
    },
    "menubar.restart_failed": {
        "it": "Riavvio fallito: {error}",
        "en": "Restart failed: {error}",
    },
    "menubar.title_hub_updates": {
        "it": "Expando ↑{count}",
        "en": "Expando ↑{count}",
    },
    "menubar.update_manual_required": {
        "it": "Scarica l'ultima versione da GitHub Releases.",
        "en": "Download the latest version from GitHub Releases.",
    },
    "menubar.updates": {"it": "Aggiorna Expando", "en": "Update Expando"},
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
    "menubar.ui_failed": {
        "it": "Impossibile aprire la finestra. Riprova o riavvia Expando.",
        "en": "Could not open the window. Try again or restart Expando.",
    },
    "menubar.action_failed": {
        "it": "Operazione non riuscita: {error}",
        "en": "Operation failed: {error}",
    },
    "menubar.toggle_enabled": {
        "it": "Espansione testo attivata",
        "en": "Text expansion enabled",
    },
    "menubar.toggle_disabled": {
        "it": "Espansione testo disattivata",
        "en": "Text expansion disabled",
    },
    "menubar.health": {"it": "Diagnostica", "en": "Diagnostics"},
    "menubar.snooze": {"it": "Pausa temporanea", "en": "Snooze"},
    "menubar.snooze.1h": {"it": "Pausa 1 ora", "en": "Snooze 1 hour"},
    "menubar.snooze.4h": {"it": "Pausa 4 ore", "en": "Snooze 4 hours"},
    "menubar.snooze.clear": {"it": "Riprendi espansione", "en": "Resume expansion"},
    "menubar.snooze.active": {
        "it": "In pausa ({remaining})",
        "en": "Snoozed ({remaining})",
    },
    "menubar.snooze.enabled": {
        "it": "Espansione in pausa per {remaining}.",
        "en": "Expansion snoozed for {remaining}.",
    },
    "menubar.snooze.cleared": {
        "it": "Pausa terminata. Espansione riattivata.",
        "en": "Snooze cleared. Expansion resumed.",
    },
    "menubar.permissions": {"it": "Configura permessi macOS", "en": "Set up macOS permissions"},
    "menubar.permissions_ok": {
        "it": "Permessi macOS OK",
        "en": "macOS permissions OK",
    },
    "menubar.permissions_missing": {
        "it": "Completa permessi macOS",
        "en": "Finish macOS permissions",
    },
    "menubar.hub_updates": {
        "it": "Aggiorna libreria snippet",
        "en": "Update snippet library",
    },
    "menubar.hub_updates_count": {
        "it": "Aggiorna libreria ({count})",
        "en": "Update library ({count})",
    },
    "menubar.hub_up_to_date": {
        "it": "Tutti i pacchetti hub sono aggiornati.",
        "en": "All hub packages are up to date.",
    },
    "menubar.hub_upgrade_title": {
        "it": "Aggiornare il pacchetto hub?",
        "en": "Upgrade this hub package?",
    },
    "menubar.hub_upgraded": {
        "it": "Pacchetto {package} aggiornato.",
        "en": "Package {package} upgraded.",
    },
    "editor.search_placeholder": {
        "it": "Cerca snippet",
        "en": "Search snippets",
    },
    "editor.window_title": {"it": "Expando — Snippet", "en": "Expando — Snippets"},
    "editor.trigger_label": {"it": "Trigger", "en": "Trigger"},
    "editor.app_label": {"it": "Solo in app", "en": "Only in app"},
    "editor.collection_label": {"it": "Raccolta", "en": "Collection"},
    "editor.text_label": {"it": "Testo", "en": "Text"},
    "editor.preview_label": {"it": "Anteprima", "en": "Preview"},
    "editor.new_button": {"it": "Nuovo", "en": "New"},
    "editor.save_button": {"it": "Salva", "en": "Save"},
    "editor.delete_button": {"it": "Elimina", "en": "Delete"},
    "editor.close_button": {"it": "Chiudi", "en": "Close"},
    "doctor.repair.launch_agent": {
        "it": "LaunchAgent reinstallato",
        "en": "LaunchAgent reinstalled",
    },
    "doctor.notarize_history.title": {
        "it": "Audit notarizzazione (storico locale)",
        "en": "Notarization audit (local history)",
    },
    "doctor.notarize_history.stats": {
        "it": "  Esecuzioni: {total} (ok={ok}, fail={failed}) · ultimi 10: {recent_rate} ok",
        "en": "  Runs: {total} (ok={ok}, fail={failed}) · last 10: {recent_rate} ok",
    },
    "doctor.notarize_history.last": {
        "it": "  Ultima: {recorded_at} {status} · pass={pass_count} warn={warn_count} fail={fail_count}",
        "en": "  Last: {recorded_at} {status} · pass={pass_count} warn={warn_count} fail={fail_count}",
    },
    "doctor.notarize_history.hint_fail": {
        "it": "  → Ultimo audit fallito: esegui expando notarize-history --limit 5",
        "en": "  → Last audit failed: run expando notarize-history --limit 5",
    },
    "doctor.marketplace.title": {
        "it": "Hub marketplace (remoto)",
        "en": "Hub marketplace (remote)",
    },
    "doctor.marketplace.remote": {"it": "Indice remoto", "en": "Remote index"},
    "doctor.marketplace.unavailable": {
        "it": "Indice remoto non disponibile",
        "en": "Remote index unavailable",
    },
    "doctor.marketplace.counts": {
        "it": "  Approvati: {approved} · community: {community}",
        "en": "  Approved: {approved} · community: {community}",
    },
    "doctor.marketplace.empty": {
        "it": "  Nessun package community installabile",
        "en": "  No installable community packages",
    },
    "doctor.marketplace.community": {
        "it": "  Package community:",
        "en": "  Community packages:",
    },
    "doctor.marketplace.package": {
        "it": "    - {package_id} ({name})",
        "en": "    - {package_id} ({name})",
    },
    "doctor.marketplace.more": {
        "it": "    … e altri {count}",
        "en": "    … and {count} more",
    },
    "doctor.marketplace.hint": {
        "it": "  → expando hub install <id>",
        "en": "  → expando hub install <id>",
    },
    "doctor.marketplace.sync": {
        "it": "  Sync remoto → locale (dry-run):",
        "en": "  Remote → local sync (dry-run):",
    },
    "doctor.marketplace.sync_counts": {
        "it": "    locale: {local_total} voci, {local_approved} approvati · remoto: {remote_approved} approvati",
        "en": "    local: {local_total} entries, {local_approved} approved · remote: {remote_approved} approved",
    },
    "doctor.marketplace.sync_stats": {
        "it": "    merge: aggiunti={added}, aggiornati={updated}, invariati={unchanged}",
        "en": "    merge: added={added}, updated={updated}, unchanged={unchanged}",
    },
    "doctor.marketplace.sync_hint": {
        "it": "→ expando hub portal sync",
        "en": "→ expando hub portal sync",
    },
    "doctor.marketplace.pending_diff": {
        "it": "  Pending marketplace (diff remoto):",
        "en": "  Marketplace pending (remote diff):",
    },
    "doctor.marketplace.pending_remote": {
        "it": "    - {package_id}: {name} ({author}) — assente in coda locale",
        "en": "    - {package_id}: {name} ({author}) — missing from local queue",
    },
    "doctor.marketplace.pending_changed": {
        "it": "    - {package_id}: metadata divergente",
        "en": "    - {package_id}: metadata differs",
    },
    "doctor.marketplace.pending_field": {
        "it": "        {field}: locale={local} · remoto={remote}",
        "en": "        {field}: local={local} · remote={remote}",
    },
    "doctor.marketplace.pending_more": {
        "it": "    … e altri {count}",
        "en": "    … and {count} more",
    },
    "doctor.marketplace.pending_hint": {
        "it": "→ expando hub portal sync",
        "en": "→ expando hub portal sync",
    },
    "doctor.marketplace.exported": {
        "it": "Report doctor+marketplace JSON esportato in {path}",
        "en": "Doctor+marketplace JSON report exported to {path}",
    },
    "doctor.marketplace.json_section": {
        "it": "--- Marketplace JSON ---",
        "en": "--- Marketplace JSON ---",
    },
    "doctor.json.exported": {
        "it": "Report doctor JSON esportato in {path}",
        "en": "Doctor JSON report exported to {path}",
    },
    "doctor.json.section": {
        "it": "--- Doctor JSON ---",
        "en": "--- Doctor JSON ---",
    },
    "doctor.full.exported": {
        "it": "Report health completo esportato in {path}",
        "en": "Full health JSON report exported to {path}",
    },
    "doctor.full.json_section": {
        "it": "--- Full health JSON ---",
        "en": "--- Full health JSON ---",
    },
    "doctor.full.html_exported": {
        "it": "Dashboard health HTML scritta in {path}",
        "en": "Health HTML dashboard written to {path}",
    },
    "doctor.crash_warning": {
        "it": "{count} crash report negli ultimi 7 giorni — esegui `expando crashes`.",
        "en": "{count} crash report(s) in the last 7 days — run `expando crashes`.",
    },
    "doctor.repair.hint": {
        "it": "Stato daemon incoerente — esegui `expando doctor --repair`.",
        "en": "Daemon state is inconsistent — run `expando doctor --repair`.",
    },
    "doctor.repair.needs_repair": {
        "it": "Riparazione consigliata: PID/lock/processi orfani rilevati.",
        "en": "Repair recommended: stale PID/lock/orphan processes detected.",
    },
    "doctor.repair.done": {
        "it": "Riparazione completata: {actions}",
        "en": "Repair completed: {actions}",
    },
    "doctor.repair.none": {
        "it": "Nessuna azione di riparazione necessaria.",
        "en": "No repair actions were needed.",
    },
    "doctor.injection_probe.skipped": {
        "it": "Probe injection: saltato ({detail})",
        "en": "Injection probe: skipped ({detail})",
    },
    "doctor.injection_probe.result": {
        "it": "Probe injection ({method}): {status} — {detail}",
        "en": "Injection probe ({method}): {status} — {detail}",
    },
    "doctor.injection_probe.failed": {
        "it": "Probe injection fallito: {detail}",
        "en": "Injection probe failed: {detail}",
    },
    "doctor.injection_degradation.status": {
        "it": "Fallimenti injection consecutivi: {count}",
        "en": "Consecutive injection failures: {count}",
    },
    "doctor.injection_degradation.warn": {
        "it": "{count} fallimenti injection consecutivi — verifica permessi e probe doctor.",
        "en": "{count} consecutive injection failures — check permissions and doctor probe.",
    },
    "doctor.injection_degradation.disabled": {
        "it": "Injection disabilitata dopo troppi fallimenti consecutivi (EXPANDO_AUTO_DISABLE_INJECTION).",
        "en": "Injection disabled after too many consecutive failures (EXPANDO_AUTO_DISABLE_INJECTION).",
    },
    "doctor.safe_mode.active": {
        "it": "Safe mode attivo: {reason}",
        "en": "Safe mode active: {reason}",
    },
    "doctor.safe_mode.line": {
        "it": "Safe mode: {reason}",
        "en": "Safe mode: {reason}",
    },
    "doctor.permissions.accessibility_missing": {
        "it": "L'espansione automatica non funzionerà finché Accessibilità non è concessa per {grant_label}.",
        "en": "Automatic expansion will not work until Accessibility is granted for {grant_label}.",
    },
    "doctor.permissions.input_monitoring_missing": {
        "it": "Monitoraggio input mancante: i trigger potrebbero non essere rilevati.",
        "en": "Input Monitoring is missing: triggers may not be detected.",
    },
    "listener.permissions.input_monitoring": {
        "it": "Monitoraggio input non concesso per {grant_label}. Abilitalo in Impostazioni → Privacy e sicurezza → Monitoraggio input.",
        "en": "Input Monitoring is not granted for {grant_label}. Enable it in System Settings → Privacy & Security → Input Monitoring.",
    },
    "listener.permissions.accessibility": {
        "it": "Accessibilità non concessa per {grant_label}. Abilitala in Impostazioni → Privacy e sicurezza → Accessibilità.",
        "en": "Accessibility is not granted for {grant_label}. Enable it in System Settings → Privacy & Security → Accessibility.",
    },
    "cli.import.header": {"it": "Importati:", "en": "Imported:"},
    "cli.import.item": {"it": "  - {name}", "en": "  - {name}"},
    "cli.backup_created": {"it": "Backup creato: {path}", "en": "Backup created: {path}"},
    "cli.pre_mutation_backup": {
        "it": "Backup pre-modifica: {path}",
        "en": "Pre-mutation backup: {path}",
    },
    "cli.support_bundle_created": {
        "it": "Support bundle creato: {path}",
        "en": "Support bundle created: {path}",
    },
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
    "cli.hub.up_to_date": {
        "it": "Tutti i pacchetti hub installati sono aggiornati.",
        "en": "All installed hub packages are up to date.",
    },
    "cli.hub.outdated_line": {
        "it": "{package}: {local} → {remote}",
        "en": "{package}: {local} → {remote}",
    },
    "cli.hub.upgraded": {
        "it": "Aggiornato {package} in {path}",
        "en": "Upgraded {package} to {path}",
    },
    "doctor.hub_updates.available": {
        "it": "{count} aggiornamenti hub disponibili: {packages} (esegui `expando hub outdated`)",
        "en": "{count} hub updates available: {packages} (run `expando hub outdated`)",
    },
    "wizard.install_launch_agent": {
        "it": "Installa avvio automatico",
        "en": "Install auto-start",
    },
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
    "benchmark.sparkle.title": {
        "it": "Sparkle / appcast",
        "en": "Sparkle / appcast",
    },
    "benchmark.sparkle.available": {
        "it": "Sparkle nativo",
        "en": "Native Sparkle",
    },
    "benchmark.sparkle.bundle": {"it": "App bundle", "en": "App bundle"},
    "benchmark.sparkle.helper": {"it": "Helper", "en": "Helper"},
    "benchmark.sparkle.framework": {"it": "Sparkle.framework", "en": "Sparkle.framework"},
    "benchmark.sparkle.appcast_fetch": {"it": "Fetch appcast", "en": "Appcast fetch"},
    "benchmark.sparkle.helper_check": {
        "it": "Helper update check",
        "en": "Helper update check",
    },
    "benchmark.sparkle.helper_slow": {
        "it": "SPARKLE_HELPER_SLOW: {ms} ms (soglia {threshold} ms)",
        "en": "SPARKLE_HELPER_SLOW: {ms} ms (threshold {threshold} ms)",
    },
    "benchmark.sparkle.helper_fail": {
        "it": "SPARKLE_HELPER_FAIL: {ms} ms (soglia {threshold} ms)",
        "en": "SPARKLE_HELPER_FAIL: {ms} ms (threshold {threshold} ms)",
    },
    "benchmark.sparkle.entries": {"it": "release", "en": "releases"},
    "benchmark.sparkle.versions": {"it": "Versioni", "en": "Versions"},
    "benchmark.sparkle.none": {"it": "n/d", "en": "n/a"},
    "sparkle.smoke.title": {
        "it": "Sparkle smoke test",
        "en": "Sparkle smoke test",
    },
    "sparkle.smoke.bundle": {"it": "App bundle", "en": "App bundle"},
    "sparkle.smoke.helper": {"it": "Helper", "en": "Helper"},
    "sparkle.smoke.framework": {"it": "Sparkle.framework", "en": "Sparkle.framework"},
    "sparkle.smoke.ok": {"it": "OK — helper firmato e framework presente", "en": "OK — helper signed and framework present"},
    "sparkle.smoke.fail": {"it": "FAIL", "en": "FAIL"},
    "benchmark.sparkle.update_available": {
        "it": "Aggiornamento disponibile",
        "en": "Update available",
    },
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
    "sync.icloud_conflicts": {
        "it": "Conflitti iCloud",
        "en": "iCloud conflicts",
    },
    "sync.conflict.git_dirty": {
        "it": "Repository git con modifiche non committate",
        "en": "Git repository has uncommitted changes",
    },
    "sync.conflict.icloud_marker": {
        "it": "Marker conflitto iCloud: {path}",
        "en": "iCloud conflict marker: {path}",
    },
    "sync.conflict.blocked": {
        "it": "Sync bloccata per conflitti: {detail}",
        "en": "Sync blocked due to conflicts: {detail}",
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
    "hub.submit.queued": {
        "it": "Package {package_id} aggiunto alla coda marketplace (pending).",
        "en": "Package {package_id} added to the marketplace queue (pending).",
    },
    "hub.submit.status.header": {
        "it": "Package {package_id}: stato {status}",
        "en": "Package {package_id}: status {status}",
    },
    "hub.submit.status.not_found": {
        "it": "Package {package_id} non trovato nel marketplace locale.",
        "en": "Package {package_id} not found in the local marketplace.",
    },
    "hub.submit.status.official": {
        "it": "Package {package_id} è nell'indice ufficiale (non in coda marketplace).",
        "en": "Package {package_id} is in the official index (not in marketplace queue).",
    },
    "hub.submit.status.submitted": {
        "it": "  Inviato: {when}",
        "en": "  Submitted: {when}",
    },
    "hub.submit.status.reviewed": {
        "it": "  Revisionato: {when}",
        "en": "  Reviewed: {when}",
    },
    "hub.submit.status.reviewer": {
        "it": "  Reviewer: {name}",
        "en": "  Reviewer: {name}",
    },
    "hub.submit.status.note": {
        "it": "  Nota: {note}",
        "en": "  Note: {note}",
    },
    "hub.submit.status.official_index": {
        "it": "  Presente anche nell'indice ufficiale.",
        "en": "  Also listed in the official index.",
    },
    "hub.submit.init.ok": {
        "it": "Template package creato: {path}",
        "en": "Package template created: {path}",
    },
    "hub.submit.init.next": {
        "it": "Modifica hub.json e snippets.yml, poi: expando hub submit run {path}",
        "en": "Edit hub.json and snippets.yml, then: expando hub submit run {path}",
    },
    "hub.validate.community.header": {
        "it": "Validazione package community ({count}):",
        "en": "Community package validation ({count}):",
    },
    "hub.validate.community.ok": {
        "it": "  ✓ {package_id} ({matches} snippet)",
        "en": "  ✓ {package_id} ({matches} snippet(s))",
    },
    "hub.validate.community.fail": {
        "it": "  ✗ {package_id}",
        "en": "  ✗ {package_id}",
    },
    "hub.validate.community.empty": {
        "it": "Nessun package community da validare.",
        "en": "No community packages to validate.",
    },
    "hub.validate.community.duplicates.header": {
        "it": "Trigger duplicati cross-package ({count}):",
        "en": "Cross-package duplicate triggers ({count}):",
    },
    "hub.validate.community.duplicates.item": {
        "it": "  ✗ {trigger} → {packages}",
        "en": "  ✗ {trigger} → {packages}",
    },
    "hub.validate.community.official.header": {
        "it": "Trigger in conflitto con package ufficiali ({count}):",
        "en": "Triggers conflicting with official packages ({count}):",
    },
    "hub.validate.community.official.item": {
        "it": "  ✗ {trigger} → community:{community} / official:{official}",
        "en": "  ✗ {trigger} → community:{community} / official:{official}",
    },
    "hub.validate.community.similar.header": {
        "it": "Trigger simili a package ufficiali ({count}, solo avviso):",
        "en": "Triggers similar to official packages ({count}, warning only):",
    },
    "hub.validate.community.similar.item": {
        "it": "  ! {community_trigger} ≈ {official_trigger} ({score}, {reason}) → community:{community} / official:{official}",
        "en": "  ! {community_trigger} ≈ {official_trigger} ({score}, {reason}) → community:{community} / official:{official}",
    },
    "hub.validate.community.html_exported": {
        "it": "Dashboard trigger HTML scritta in {path}",
        "en": "Trigger dashboard HTML written to {path}",
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
        "it": "Sito marketplace pubblicato: {html} · JSON: {json} · trigger dashboard: {suggestions} · maintainer portal: {maintainer} · community validation: {validation} · health dashboard: {health_html} · doctor JSON: {health_json} · hub index: {hub_index} · package approvati: {count}",
        "en": "Marketplace site published: {html} · JSON: {json} · trigger dashboard: {suggestions} · maintainer portal: {maintainer} · community validation: {validation} · health dashboard: {health_html} · doctor JSON: {health_json} · hub index: {hub_index} · approved packages: {count}",
    },
    "hub.portal.pending_diff.title": {
        "it": "Diff metadata pending marketplace ({count}):",
        "en": "Marketplace pending metadata diff ({count}):",
    },
    "hub.portal.pending_diff.empty": {
        "it": "Nessuna differenza pending tra remoto e coda locale.",
        "en": "No pending metadata differences between remote and local queue.",
    },
    "hub.portal.pending_diff.exported": {
        "it": "Diff pending esportato in {path}",
        "en": "Pending diff exported to {path}",
    },
    "sparkle.benchmark.history.title": {
        "it": "Storico benchmark Sparkle helper",
        "en": "Sparkle helper benchmark history",
    },
    "sparkle.benchmark.history.path": {"it": "File", "en": "File"},
    "sparkle.benchmark.history.stats": {
        "it": "Esecuzioni: {total} (lente={slow}) · ultima: {last_ms} ms",
        "en": "Runs: {total} (slow={slow}) · last: {last_ms} ms",
    },
    "sparkle.benchmark.history.na": {"it": "n/d", "en": "n/a"},
    "sparkle.benchmark.history.empty": {
        "it": "Nessuna esecuzione registrata — usa expando sparkle-benchmark-history record",
        "en": "No recorded runs — use expando sparkle-benchmark-history record",
    },
    "sparkle.benchmark.history.recent": {
        "it": "Ultime {limit} esecuzioni:",
        "en": "Last {limit} runs:",
    },
    "sparkle.benchmark.history.entry": {
        "it": "  {recorded_at}  v{version}  helper={helper_ms} ms  slow={slow}",
        "en": "  {recorded_at}  v{version}  helper={helper_ms} ms  slow={slow}",
    },
    "sparkle.benchmark.history.recorded": {
        "it": "Registrato in {path} ({recorded_at})",
        "en": "Recorded in {path} ({recorded_at})",
    },
    "sparkle.benchmark.history.svg_written": {
        "it": "Grafico trend SVG scritto in {path}",
        "en": "Trend SVG chart written to {path}",
    },
    "sparkle.benchmark.history.exported": {
        "it": "Storico benchmark esportato in {path}",
        "en": "Benchmark history exported to {path}",
    },
    "sparkle.benchmark.history.trend": {
        "it": "Trend helper: {sparkline}  min={min_ms} ms · max={max_ms} ms · avg={avg_ms} ms",
        "en": "Helper trend: {sparkline}  min={min_ms} ms · max={max_ms} ms · avg={avg_ms} ms",
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
