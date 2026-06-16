from __future__ import annotations

import ctypes
import ctypes.util
import platform
import subprocess
from dataclasses import dataclass


@dataclass
class PermissionStatus:
    accessibility: bool | None
    input_monitoring: bool | None
    notes: list[str]


def _check_accessibility_macos() -> bool | None:
    if platform.system() != "Darwin":
        return None
    try:
        app_services = ctypes.CDLL(
            ctypes.util.find_library("ApplicationServices") or "ApplicationServices"
        )
        app_services.AXIsProcessTrusted.restype = ctypes.c_bool
        return bool(app_services.AXIsProcessTrusted())
    except Exception:
        return None


def _check_input_monitoring_macos() -> bool | None:
    if platform.system() != "Darwin":
        return None
    try:
        result = subprocess.run(
            [
                "sqlite3",
                "/Library/Application Support/com.apple.TCC/TCC.db",
                "SELECT allowed FROM access WHERE service='kTCCServiceListenEvent';",
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode != 0:
            return None
        return "1" in result.stdout
    except Exception:
        return None


def check_permissions() -> PermissionStatus:
    notes: list[str] = []
    accessibility = _check_accessibility_macos()
    input_monitoring = _check_input_monitoring_macos()

    if platform.system() == "Darwin":
        if accessibility is False:
            notes.append(
                "Accessibilità non concessa: abilita Expando.app o Python in "
                "Impostazioni → Privacy → Accessibilità"
            )
        if input_monitoring is False:
            notes.append(
                "Monitoraggio input non concesso: opzionale, ma consigliato in "
                "Impostazioni → Privacy → Monitoraggio input"
            )
        if accessibility is None:
            notes.append("Impossibile verificare Accessibilità automaticamente")
    else:
        notes.append("Verifica permessi disponibile solo su macOS")

    return PermissionStatus(
        accessibility=accessibility,
        input_monitoring=input_monitoring,
        notes=notes,
    )