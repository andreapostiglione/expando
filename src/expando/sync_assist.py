from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .i18n import t, tf
from .paths import default_config_dir

ICLOUD_DOCS = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
SYNC_PATHS = ("config", "match", "plugins")
IGNORED_RUNTIME_FILES = (
    "expando.pid",
    "expando.lock",
    "expando.log",
    "expansion_stats.json",
    ".last_seen_version",
    ".last_update_check",
)


@dataclass
class SyncStatus:
    config_dir: Path
    resolved_dir: Path
    is_symlink: bool
    symlink_target: Path | None
    mode: str
    git_repo: bool
    git_dirty: bool
    icloud_backed: bool


def _run_git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str] | None:
    if shutil.which("git") is None:
        return None
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def inspect_sync_status(config_dir: Path) -> SyncStatus:
    config_dir = config_dir.expanduser()
    resolved = config_dir.resolve()
    is_symlink = config_dir.is_symlink()
    target = resolved if is_symlink else None
    icloud_backed = False
    mode = "local"

    if is_symlink and target is not None:
        mode = "symlink"
        try:
            icloud_backed = str(target).startswith(str(ICLOUD_DOCS.resolve()))
        except OSError:
            icloud_backed = False
        if icloud_backed:
            mode = "icloud"

    git_repo = (resolved / ".git").exists()
    git_dirty = False
    if git_repo:
        if mode == "local":
            mode = "git"
        elif "+" not in mode:
            mode = f"{mode}+git"
        status = _run_git(["status", "--porcelain"], cwd=resolved)
        if status is not None and status.returncode == 0:
            git_dirty = bool(status.stdout.strip())

    return SyncStatus(
        config_dir=config_dir,
        resolved_dir=resolved,
        is_symlink=is_symlink,
        symlink_target=target,
        mode=mode,
        git_repo=git_repo,
        git_dirty=git_dirty,
        icloud_backed=icloud_backed,
    )


def format_sync_report(status: SyncStatus) -> str:
    lines = [
        f"{t('sync.config_dir')}: {status.config_dir}",
        f"{t('sync.resolved')}: {status.resolved_dir}",
        f"{t('sync.mode')}: {status.mode}",
    ]
    if status.is_symlink and status.symlink_target:
        lines.append(f"{t('sync.symlink_target')}: {status.symlink_target}")
    if status.git_repo:
        dirty = t("sync.git_dirty") if status.git_dirty else t("sync.git_clean")
        lines.append(f"{t('sync.git')}: {dirty}")
    else:
        lines.append(f"{t('sync.git')}: {t('sync.git_none')}")
    lines.append("")
    lines.append(t("sync.paths_hint"))
    for name in SYNC_PATHS:
        path = status.resolved_dir / name
        marker = "✓" if path.exists() else "—"
        lines.append(f"  {marker} {name}/")
    return "\n".join(lines)


def _gitignore_content() -> str:
    lines = ["# Expando runtime files — do not sync", *IGNORED_RUNTIME_FILES, "crashes/"]
    return "\n".join(lines) + "\n"


def init_git_sync(config_dir: Path, *, commit: bool = False) -> list[str]:
    config_dir = config_dir.expanduser()
    config_dir.mkdir(parents=True, exist_ok=True)
    messages: list[str] = []

    if shutil.which("git") is None:
        raise RuntimeError(t("sync.git_missing"))

    if not (config_dir / ".git").exists():
        result = subprocess.run(
            ["git", "init"],
            cwd=config_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "git init failed")
        messages.append(t("sync.git_initialized"))

    gitignore = config_dir / ".gitignore"
    content = _gitignore_content()
    if not gitignore.exists() or gitignore.read_text(encoding="utf-8") != content:
        gitignore.write_text(content, encoding="utf-8")
        messages.append(t("sync.gitignore_written"))

    for name in SYNC_PATHS:
        (config_dir / name).mkdir(parents=True, exist_ok=True)

    if commit:
        subprocess.run(["git", "add", ".gitignore", *SYNC_PATHS], cwd=config_dir, check=False)
        status = _run_git(["status", "--porcelain"], cwd=config_dir)
        if status and status.stdout.strip():
            commit_result = subprocess.run(
                ["git", "commit", "-m", "Expando config sync"],
                cwd=config_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            if commit_result.returncode == 0:
                messages.append(t("sync.git_committed"))
            else:
                messages.append(commit_result.stderr.strip() or t("sync.git_commit_skipped"))
        else:
            messages.append(t("sync.git_commit_skipped"))

    messages.append(t("sync.git_next_steps"))
    return messages


def setup_icloud_symlink(
    config_dir: Path | None = None,
    *,
    folder_name: str = "expando-config",
    dry_run: bool = False,
) -> list[str]:
    if platform.system() != "Darwin":
        raise RuntimeError(t("sync.icloud_macos_only"))

    config_dir = (config_dir or default_config_dir()).expanduser()
    icloud_root = ICLOUD_DOCS
    if not icloud_root.exists():
        raise RuntimeError(t("sync.icloud_unavailable"))

    target = icloud_root / folder_name
    messages: list[str] = []

    if config_dir.is_symlink():
        messages.append(t("sync.already_linked"))
        messages.append(str(config_dir.resolve()))
        return messages

    has_data = config_dir.exists() and any(config_dir.iterdir())

    if dry_run:
        messages.append(t("sync.dry_run"))
        if has_data:
            messages.append(
                tf("sync.would_backup", path=str(config_dir.parent / f"{config_dir.name}.pre-icloud-backup"))
            )
        messages.append(f"  mkdir -p {target}")
        for name in SYNC_PATHS:
            if (config_dir / name).exists():
                messages.append(f"  copy {name}/ → {target / name}")
        messages.append(f"  ln -s {target} {config_dir}")
        return messages

    if has_data:
        backup = config_dir.parent / f"{config_dir.name}.pre-icloud-backup"
        if backup.exists():
            raise RuntimeError(t("sync.backup_exists"))
        shutil.move(str(config_dir), str(backup))
        messages.append(tf("sync.backup_created", path=backup))
        source_root = backup
    else:
        if config_dir.exists():
            config_dir.rmdir()
        source_root = None

    target.mkdir(parents=True, exist_ok=True)
    if source_root is not None:
        for name in SYNC_PATHS:
            src = source_root / name
            if not src.exists():
                continue
            dest = target / name
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            if src.is_dir():
                shutil.copytree(src, dest)
            else:
                shutil.copy2(src, dest)

    for name in SYNC_PATHS:
        (target / name).mkdir(parents=True, exist_ok=True)

    config_dir.symlink_to(target)
    messages.append(t("sync.icloud_linked"))
    messages.append(str(target))
    messages.append(t("sync.icloud_hint"))
    return messages