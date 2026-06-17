from __future__ import annotations

from pathlib import Path

import click

from .i18n import t, tf


def echo_imported_files(names: list[str]) -> None:
    click.echo(t("cli.import.header"))
    for name in names:
        click.echo(tf("cli.import.item", name=name))


def echo_espanso_import_report(report, *, backup_path: Path | None = None) -> None:
    if backup_path is not None:
        click.echo(tf("cli.backup_created", path=backup_path))
    click.echo(tf("cli.imported_from", source=report.source))
    if report.config_merged:
        click.echo(t("cli.config_merged"))
    click.echo(
        tf(
            "cli.matches_imported",
            count=report.matches_imported,
            files=len(report.match_files),
        )
    )
    if report.matches_skipped:
        click.echo(tf("cli.matches_skipped", count=report.matches_skipped))
    for warning in report.warnings:
        click.echo(tf("cli.warning", message=warning))


def echo_external_import_report(report, *, backup_path: Path | None = None) -> None:
    if backup_path is not None:
        click.echo(tf("cli.backup_created", path=backup_path))
    click.echo(tf("cli.imported_from", source=report.source))
    click.echo(
        tf(
            "cli.matches_imported",
            count=report.matches_imported,
            files=len(report.match_files),
        )
    )
    if report.matches_skipped:
        click.echo(tf("cli.snippets_skipped", count=report.matches_skipped))
    for name in report.match_files:
        click.echo(tf("cli.wrote_file", name=name))
    for warning in report.warnings:
        click.echo(tf("cli.warning", message=warning))