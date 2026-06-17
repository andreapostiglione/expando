from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .backup import backup_config
from .espanso_import import EspansoImportReport, import_espanso_config


@dataclass
class EspansoMigrateReport:
    backup_path: Path
    import_report: EspansoImportReport


def migrate_espanso_config(
    config_dir: Path,
    *,
    source: Path | None = None,
    force: bool = False,
) -> EspansoMigrateReport:
    backup_path = backup_config(config_dir)
    import_report = import_espanso_config(
        config_dir,
        source=source,
        force=force,
    )
    return EspansoMigrateReport(
        backup_path=backup_path,
        import_report=import_report,
    )