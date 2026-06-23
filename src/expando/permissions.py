from __future__ import annotations

import ctypes
import ctypes.util
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .runtime_info import RuntimeInfo, detect_runtime

SETTINGS_ACCESSIBILITY = (
    "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
)
SETTINGS_INPUT_MONITORING = (
    "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent"
)

_TCC_ALLOWED = {1, 2, 4}


@dataclass
class PermissionStatus:
    accessibility: bool | None
    input_monitoring: bool | None
    notes: list[str]
    clipboard: bool | None = None
    runtime: RuntimeInfo | None = None
    injection_ready: bool | None = None


def _check_accessibility_macos(*, prompt: bool = False) -> bool | None:
    if platform.system() != "Darwin":
        return None
    try:
        app_services = ctypes.CDLL(
            ctypes.util.find_library("ApplicationServices") or "ApplicationServices"
        )
        app_services.AXIsProcessTrusted.restype = ctypes.c_bool
        if prompt:
            options = ctypes.c_void_p(
                ctypes.c_char_p(
                    b'<?xml version="1.0" encoding="UTF-8"?>'
                    b'<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                    b'"http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
                    b'<plist version="1.0"><dict>'
                    b'<key>AXTrustedCheckOptionPrompt</key><true/>'
                    b"</dict></plist>"
                )
            )
            app_services.AXIsProcessTrustedWithOptions.restype = ctypes.c_bool
            app_services.AXIsProcessTrustedWithOptions.argtypes = [ctypes.c_void_p]
            return bool(app_services.AXIsProcessTrustedWithOptions(options))
        return bool(app_services.AXIsProcessTrusted())
    except Exception:
        return None


def _tcc_db_paths() -> list[Path]:
    return [
        Path.home() / "Library/Application Support/com.apple.TCC/TCC.db",
        Path("/Library/Application Support/com.apple.TCC/TCC.db"),
    ]


def _query_tcc(service: str) -> list[tuple[str, int]]:
    rows: list[tuple[str, int]] = []
    for db in _tcc_db_paths():
        if not db.exists():
            continue
        try:
            result = subprocess.run(
                [
                    "sqlite3",
                    str(db),
                    "SELECT client, auth_value FROM access "
                    f"WHERE service='{service}';",
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )
        except Exception:
            continue
        if result.returncode != 0:
            continue
        for line in result.stdout.splitlines():
            if "|" not in line:
                continue
            client, raw_value = line.split("|", 1)
            try:
                rows.append((client.strip(), int(raw_value.strip())))
            except ValueError:
                continue
        if rows:
            return rows
    return rows


def _client_matches_runtime(client: str, runtime: RuntimeInfo) -> bool:
    client_lower = client.casefold()
    labels = {
        runtime.grant_label.casefold(),
        Path(runtime.executable).name.casefold(),
        "expando.app",
        "expando",
        "python",
        "python3",
        "python3.14",
        "python3.12",
    }
    return any(label and label in client_lower for label in labels)


def _read_clipboard_text() -> str | None:
    try:
        result = subprocess.run(
            ["pbpaste"],
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        )
    except Exception:
        return None
    return result.stdout


def _write_clipboard_text(text: str) -> None:
    subprocess.run(["pbcopy"], input=text, text=True, check=True, timeout=2)


def _check_clipboard_macos() -> bool | None:
    if platform.system() != "Darwin":
        return None
    probe = "expando-clipboard-probe"
    original = _read_clipboard_text()
    try:
        _write_clipboard_text(probe)
        result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=2, check=True)
        return result.stdout == probe
    except Exception:
        return None
    finally:
        if original is not None:
            try:
                _write_clipboard_text(original)
            except Exception:
                pass


def _check_input_monitoring_macos(runtime: RuntimeInfo) -> bool | None:
    if platform.system() != "Darwin":
        return None
    rows = _query_tcc("kTCCServiceListenEvent")
    if not rows:
        return None
    matched = [
        auth for client, auth in rows
        if _client_matches_runtime(client, runtime) and auth in _TCC_ALLOWED
    ]
    if matched:
        return True
    return False


def open_accessibility_settings() -> None:
    if platform.system() != "Darwin":
        return
    subprocess.run(["open", SETTINGS_ACCESSIBILITY], check=False)


def open_input_monitoring_settings() -> None:
    if platform.system() != "Darwin":
        return
    subprocess.run(["open", SETTINGS_INPUT_MONITORING], check=False)


def check_permissions(
    *,
    prompt_accessibility: bool = False,
    include_clipboard: bool = True,
) -> PermissionStatus:
    notes: list[str] = []
    runtime = detect_runtime() if platform.system() == "Darwin" else None
    accessibility = _check_accessibility_macos(prompt=prompt_accessibility)
    input_monitoring = (
        _check_input_monitoring_macos(runtime) if runtime is not None else None
    )
    clipboard = (
        _check_clipboard_macos()
        if platform.system() == "Darwin" and include_clipboard
        else None
    )
    injection_ready = _injection_ready(accessibility, input_monitoring)

    if platform.system() == "Darwin" and runtime is not None:
        if runtime.mode == "app":
            notes.append(
                "Modalità app: abilita Expando.app in Accessibilità e Monitoraggio input."
            )
        else:
            notes.append(
                f"Modalità {runtime.mode}: macOS autorizza «{runtime.grant_label}», "
                "non «Expando». Cerca Python o il terminale in Impostazioni → Privacy."
            )
        if accessibility is False:
            notes.append(
                f"Accessibilità mancante per {runtime.grant_label}. "
                f"Percorso: {runtime.grant_hint}"
            )
        if input_monitoring is False:
            notes.append(
                "Monitoraggio input mancante: i trigger potrebbero non essere rilevati."
            )
        if accessibility is None:
            notes.append("Impossibile verificare Accessibilità automaticamente.")
        if input_monitoring is None:
            notes.append(
                "Impossibile verificare Monitoraggio input dal database TCC."
            )
        if clipboard is False:
            notes.append(
                "Clipboard non disponibile: l'iniezione via pbcopy/pbpaste potrebbe fallire."
            )
        if clipboard is None:
            notes.append("Impossibile verificare l'accesso alla clipboard.")
    else:
        notes.append("Verifica permessi disponibile solo su macOS.")

    return PermissionStatus(
        accessibility=accessibility,
        input_monitoring=input_monitoring,
        clipboard=clipboard,
        notes=notes,
        runtime=runtime,
        injection_ready=injection_ready,
    )


def clipboard_injection_ready() -> bool | None:
    if platform.system() != "Darwin":
        return None
    accessibility = _check_accessibility_macos()
    clipboard = _check_clipboard_macos()
    if accessibility is False or clipboard is False:
        return False
    if accessibility is True and clipboard is True:
        return True
    return None


def _injection_ready(
    accessibility: bool | None,
    input_monitoring: bool | None,
) -> bool | None:
    if accessibility is False or input_monitoring is False:
        return False
    if accessibility is True and input_monitoring is not False:
        return True
    return None


def permissions_ready(status: PermissionStatus) -> bool:
    if status.accessibility is not True:
        return False
    if status.input_monitoring is False:
        return False
    return True