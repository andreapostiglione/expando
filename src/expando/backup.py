from __future__ import annotations

import shutil
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path


def _safe_extract(archive: tarfile.TarFile, destination: Path) -> None:
    for member in archive.getmembers():
        target = (destination / member.name).resolve()
        if not str(target).startswith(str(destination.resolve())):
            raise ValueError(f"Unsafe path in archive: {member.name}")
    if hasattr(archive, "extractall"):
        try:
            archive.extractall(destination, filter="data")
            return
        except TypeError:
            pass
    archive.extractall(destination)


def backup_config(config_dir: Path, destination: Path | None = None) -> Path:
    config_dir.mkdir(parents=True, exist_ok=True)
    if destination is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        destination = config_dir.parent / f"expando-backup-{stamp}.tar.gz"
    destination = destination.expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(destination, "w:gz") as archive:
        archive.add(config_dir, arcname=config_dir.name)
    return destination


def restore_config(config_dir: Path, archive_path: Path) -> None:
    archive_path = archive_path.expanduser()
    if not archive_path.exists():
        raise FileNotFoundError(f"Backup not found: {archive_path}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with tarfile.open(archive_path, "r:gz") as archive:
            _safe_extract(archive, temp_path)
            members = archive.getnames()
        top_level = {name.split("/")[0] for name in members}
        if not top_level:
            raise ValueError("Backup archive is empty")
        extracted = temp_path / next(iter(top_level))
        if not extracted.exists():
            raise ValueError("Backup archive does not contain a valid config directory")

        if config_dir.exists():
            backup_config(config_dir, config_dir.parent / "expando-pre-restore-backup.tar.gz")
            shutil.rmtree(config_dir)

        shutil.copytree(extracted, config_dir)