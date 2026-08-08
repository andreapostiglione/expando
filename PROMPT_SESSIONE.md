# Expando — sessione compatta

**Repo:** https://github.com/andreapostiglione/expando  
**Versione:** 3.29.25 | **Branch:** main  
**Team ID:** 68Q8CQBQQV (Inochi Srl Developer ID)

## Ultima sessione (2026-08-08) — expansion reliability

### Problema utente
- Trigger `:grok` / `:claude` richiedevano più tentativi
- Lag di digitazione rispetto ad altri expander
- Dopo un expand OK, sulla stessa riga delete + secondo trigger falliva
- Residui tipo `:grogrok` (delete incompleto + paste)

### Cause
1. **Input Monitoring** su `python3.14` non copriva `Expando.app` (poi fixato in System Settings)
2. **Char su key-release** + tastiera IT (Shift+`:`) → carattere perso o `.` invece di `:`
3. **Shift+Left delete** non funziona nei terminali → un solo backspace effettivo
4. **Mute inject 450ms** → tasti del secondo trigger ignorati
5. **Secure Input AX/osascript ~300ms** su path event-tap → lag
6. **Doppi processi** LaunchAgent + start manuale

### Fix in 3.29.25
- Listener: printable chars su **press**; space/enter/tab su release
- Injector: solo backspace affidabili; settle pre-paste
- Inject mute corto (~80ms) + `clear_buffer` post-expand
- Secure Input: se Carbon = false, skip AX
- Cache frontmost app (150ms) + cache profili YAML mtime
- Engine settle 30ms pre-delete (char su key-down)

### Config utente locale (Application Support, non in repo)
- `backend: clipboard` / `clipboard_threshold: 1`
- `force_clipboard: true` su claude/grok
- Alias: `;grok`, `//grok`, `//claude` (dev.yml locale)

### Verifica
- `expando doctor` → Accessibilità + Input Monitoring + injection OK
- 1 solo processo
- `pytest tests/test_listener.py` + secure_input tests

## Storico
- v3.29.24 e precedenti: vedi CHANGELOG.md / ROADMAP.md

## Prossimi passi (opzionali)
- Release DMG/appcast 3.29.25 + Homebrew cask bump
- Queue asincrona fuori dall’event-tap per lag digitazione residuale
- Trigger default senza `:` nei default package (layout non-US)
