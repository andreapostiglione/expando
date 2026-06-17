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
}


def t(key: str, *, locale: str | None = None) -> str:
    lang = (locale or _LOCALE).lower()
    entry = _STRINGS.get(key, {})
    if lang in entry:
        return entry[lang]
    if "en" in entry:
        return entry["en"]
    return key