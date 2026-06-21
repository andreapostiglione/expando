from __future__ import annotations

import shutil
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path


def backup_label(path: Path) -> str:
    """Turn ``expando-backup-YYYYMMDD-HHMMSS.tar.gz`` into a readable stamp."""
    name = path.name
    if name.startswith("expando-backup-") and name.endswith(".tar.gz"):
        stamp = name[len("expando-backup-") : -len(".tar.gz")]
        try:
            dt = datetime.strptime(stamp, "%Y%m%d-%H%M%S")
            return dt.strftime("%d/%m/%Y %H:%M")
        except ValueError:
            pass
    return name


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


def list_backup_archives(config_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    candidates.extend(config_dir.parent.glob("expando-backup-*.tar.gz"))
    candidates.extend(config_dir.parent.glob("expando-pre-restore-backup.tar.gz"))
    backups_dir = config_dir / "backups"
    if backups_dir.is_dir():
        candidates.extend(backups_dir.glob("*.tar.gz"))
    unique: dict[str, Path] = {}
    for path in candidates:
        if path.is_file():
            unique[str(path.resolve())] = path
    return sorted(unique.values(), key=lambda item: item.stat().st_mtime, reverse=True)


def list_restore_candidates(config_dir: Path) -> list[Path]:
    """Manual backups suitable for menu restore (excludes automatic pre-restore snapshots)."""
    return [
        path
        for path in list_backup_archives(config_dir)
        if path.name != "expando-pre-restore-backup.tar.gz"
    ]


def backups_for_picker(config_dir: Path) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for index, path in enumerate(list_restore_candidates(config_dir)):
        items.append(
            {
                "id": str(index),
                "trigger": path.name,
                "label": backup_label(path),
                "preview": str(path),
                "archive_path": str(path.resolve()),
            }
        )
    return items


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
        top_level = sorted({name.split("/")[0] for name in members})
        if not top_level:
            raise ValueError("Backup archive is empty")
        extracted = temp_path / top_level[0]
        if not extracted.exists():
            raise ValueError("Backup archive does not contain a valid config directory")

        staging_parent = Path(tempfile.mkdtemp(prefix="expando-restore-", dir=config_dir.parent))
        staged = staging_parent / config_dir.name
        rollback: Path | None = None
        try:
            shutil.copytree(extracted, staged)
            if config_dir.exists():
                backup_config(config_dir, config_dir.parent / "expando-pre-restore-backup.tar.gz")
                rollback = config_dir.parent / f".{config_dir.name}.rollback"
                if rollback.exists():
                    shutil.rmtree(rollback)
                config_dir.rename(rollback)
            shutil.move(str(staged), str(config_dir))
        except Exception:
            if not config_dir.exists() and rollback is not None and rollback.exists():
                rollback.rename(config_dir)
            raise
        finally:
            if rollback is not None and rollback.exists():
                shutil.rmtree(rollback, ignore_errors=True)
            shutil.rmtree(staging_parent, ignore_errors=True)