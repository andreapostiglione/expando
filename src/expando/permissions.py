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


@dataclass(frozen=True)
class _TCCRow:
    client: str
    client_type: int | None
    auth_value: int
    last_modified: int


def _check_accessibility_macos(
    *,
    prompt: bool = False,
    runtime: RuntimeInfo | None = None,
) -> bool | None:
    if platform.system() != "Darwin":
        return None
    if runtime is not None:
        tcc_status = _tcc_permission_for_runtime("kTCCServiceAccessibility", runtime)
        if tcc_status is not None:
            return tcc_status
    pyobjc_status = _check_accessibility_pyobjc(prompt=prompt)
    if pyobjc_status is not None:
        return pyobjc_status
    return _check_accessibility_ctypes(prompt=prompt)


def _check_accessibility_pyobjc(*, prompt: bool = False) -> bool | None:
    try:
        import HIServices

        if prompt:
            options = {HIServices.kAXTrustedCheckOptionPrompt: True}
            return bool(HIServices.AXIsProcessTrustedWithOptions(options))
        return bool(HIServices.AXIsProcessTrusted())
    except Exception:
        return None


def _check_accessibility_ctypes(*, prompt: bool = False) -> bool | None:
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


def _query_tcc(service: str) -> list[_TCCRow]:
    rows: list[_TCCRow] = []
    for db in _tcc_db_paths():
        if not db.exists():
            continue
        try:
            result = subprocess.run(
                [
                    "sqlite3",
                    str(db),
                    "SELECT client, client_type, auth_value, last_modified FROM access "
                    f"WHERE service='{service}';",
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )
        except Exception:
            continue
        if result.returncode != 0:
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
            parts = line.split("|")
            try:
                if len(parts) >= 4:
                    client, client_type, raw_value, last_modified = parts[:4]
                    rows.append(
                        _TCCRow(
                            client=client.strip(),
                            client_type=int(client_type.strip()),
                            auth_value=int(raw_value.strip()),
                            last_modified=int(last_modified.strip() or "0"),
                        )
                    )
                else:
                    client, raw_value = parts[:2]
                    rows.append(
                        _TCCRow(
                            client=client.strip(),
                            client_type=None,
                            auth_value=int(raw_value.strip()),
                            last_modified=0,
                        )
                    )
            except ValueError:
                continue
    return rows


def _client_matches_runtime(client: str, runtime: RuntimeInfo) -> bool:
    client_lower = client.casefold()
    executable = Path(runtime.executable)
    executable_name = executable.name.casefold()

    candidate_paths = {str(executable).casefold()}
    try:
        candidate_paths.add(str(executable.resolve()).casefold())
    except OSError:
        pass
    if client_lower in candidate_paths:
        return True
    if client.startswith("/"):
        try:
            if str(Path(client).resolve()).casefold() in candidate_paths:
                return True
        except OSError:
            pass
        if Path(client).name.casefold() == executable_name:
            version_hint = _python_version_hint(runtime)
            if version_hint and version_hint in client_lower:
                return True

    if runtime.mode == "app":
        return client_lower in {
            "com.andreapostiglione.expando",
            "expando.app",
            "expando",
        } or client_lower.endswith("/expando.app")

    return client_lower == runtime.grant_label.casefold()


def _python_version_hint(runtime: RuntimeInfo) -> str | None:
    name = Path(runtime.executable).name.casefold()
    if name.startswith("python3."):
        return name
    parts = Path(runtime.executable).parts
    for index, part in enumerate(parts):
        if part == "Versions" and index + 1 < len(parts):
            version = parts[index + 1]
            if version.count(".") == 1 and version.replace(".", "").isdigit():
                return f"python{version}"
    return None


def _tcc_permission_for_runtime(service: str, runtime: RuntimeInfo) -> bool | None:
    rows = _query_tcc(service)
    if not rows:
        return None
    matched = [row for row in rows if _client_matches_runtime(row.client, runtime)]
    if not matched:
        return None
    latest = max(matched, key=lambda row: row.last_modified)
    return latest.auth_value in _TCC_ALLOWED


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
    matched = [row for row in rows if _client_matches_runtime(row.client, runtime)]
    if not matched:
        return False
    latest = max(matched, key=lambda row: row.last_modified)
    return latest.auth_value in _TCC_ALLOWED


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
    include_clipboard: bool = False,
) -> PermissionStatus:
    notes: list[str] = []
    runtime = detect_runtime() if platform.system() == "Darwin" else None
    accessibility = _check_accessibility_macos(
        prompt=prompt_accessibility,
        runtime=runtime,
    )
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
            if accessibility is not True or input_monitoring is not True:
                notes.append(
                    "Modalità app: abilita Expando.app in Accessibilità e Monitoraggio input."
                )
        elif runtime.mode == "packaged":
            if accessibility is not True or input_monitoring is not True:
                notes.append(
                    "Installazione legacy: macOS sta mostrando un runtime Python "
                    f"(«{runtime.grant_label}») invece di Expando.app. "
                    "Aggiorna o reinstalla Expando."
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
