from __future__ import annotations

import os
import subprocess
from pathlib import Path

import click

from . import __version__
from .daemon import is_running, start_daemon, stop_daemon
from .paths import default_config_dir, ensure_default_config, log_file, match_dir, package_root
from .log_viewer import print_log_tail
from .doctor_checks import format_doctor_report, run_doctor
from .onboarding import run_onboarding
from .backup import backup_config, restore_config
from .match_store import (
    append_match,
    duplicate_snippet,
    export_snippet_yaml,
    format_match_list,
    import_matches,
)
from .packages import list_installed_packages
from .renderer import render_match_interactive
from .search import build_search_items, pick_snippet, resolve_snippet_text
from .app_context import get_frontmost_context, match_allowed
from .config import active_bundle, load_config, load_matches
from .cli_output import echo_espanso_import_report, echo_external_import_report, echo_imported_files
from .i18n import t, tf


def _resolve_config_dir(config_dir: str | None) -> Path:
    return Path(config_dir).expanduser() if config_dir else default_config_dir()


@click.group()
@click.version_option(__version__, prog_name="expando")
@click.option("--config-dir", type=click.Path(), default=None, help="Override config directory")
@click.pass_context
def main(ctx: click.Context, config_dir: str | None) -> None:
    resolved = _resolve_config_dir(config_dir)
    ensure_default_config(resolved, package_root())
    ctx.ensure_object(dict)
    ctx.obj["config_dir"] = resolved


@main.command()
@click.pass_context
def path(ctx: click.Context) -> None:
    """Print the configuration directory path."""
    click.echo(ctx.obj["config_dir"])


@main.command()
@click.argument("target", required=False, default="match/base.yml")
@click.pass_context
def edit(ctx: click.Context, target: str) -> None:
    """Open a configuration file in $EDITOR."""
    config_dir: Path = ctx.obj["config_dir"]
    if not target.endswith((".yml", ".yaml")):
        if (config_dir / "match" / f"{target}.yml").exists() or target.startswith("match/"):
            target = f"match/{target}.yml" if "/" not in target else target
            if not target.endswith((".yml", ".yaml")):
                target += ".yml"
        elif (config_dir / "config" / f"{target}.yml").exists() or target.startswith("config/"):
            target = f"config/{target}.yml" if "/" not in target else target
            if not target.endswith((".yml", ".yaml")):
                target += ".yml"
        else:
            target = f"match/{target}.yml"

    file_path = config_dir / target
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        file_path.write_text("matches:\n", encoding="utf-8")

    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "nano"
    subprocess.run([editor, str(file_path)], check=False)


@main.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show daemon status."""
    config_dir: Path = ctx.obj["config_dir"]
    running, pid = is_running(config_dir)
    if running:
        click.echo(tf("cli.status.running", pid=pid))
    else:
        click.echo(t("cli.status.stopped"))


@main.command()
@click.pass_context
def start(ctx: click.Context) -> None:
    """Start the background daemon."""
    config_dir: Path = ctx.obj["config_dir"]
    pid = start_daemon(config_dir)
    click.echo(tf("cli.started", pid=pid))


@main.command()
@click.pass_context
def stop(ctx: click.Context) -> None:
    """Stop the background daemon."""
    config_dir: Path = ctx.obj["config_dir"]
    if stop_daemon(config_dir):
        click.echo(t("cli.stopped"))
    else:
        click.echo(t("cli.not_running"))


@main.command()
@click.pass_context
def restart(ctx: click.Context) -> None:
    """Restart the background daemon."""
    config_dir: Path = ctx.obj["config_dir"]
    stop_daemon(config_dir)
    pid = start_daemon(config_dir)
    click.echo(tf("cli.restarted", pid=pid))


@main.command()
@click.pass_context
def run(ctx: click.Context) -> None:
    """Run in foreground (for debugging)."""
    from .daemon import foreground

    foreground(ctx.obj["config_dir"])


def _find_match_for_trigger(trigger: str, matches):
    for item in matches:
        if trigger in item.triggers:
            return item
        if item.ignore_case and any(
            trigger.casefold() == candidate.casefold() for candidate in item.triggers
        ):
            return item
    return None


@main.command("match")
@click.argument("trigger")
@click.option(
    "--check",
    is_flag=True,
    help="Show whether the trigger is allowed in the current app.",
)
@click.pass_context
def match_cmd(ctx: click.Context, trigger: str, check: bool) -> None:
    """Test-render a trigger without typing."""
    config_dir: Path = ctx.obj["config_dir"]
    bundle = active_bundle(config_dir, load_config(config_dir))
    item = _find_match_for_trigger(trigger, bundle.matches)
    if item is None:
        raise click.ClickException(tf("cli.trigger_not_found", trigger=trigger))

    if check:
        context = get_frontmost_context()
        allowed = match_allowed(
            context,
            global_blacklist=bundle.app.app_blacklist,
            if_app=item.if_app or None,
            unless_app=item.unless_app or None,
            if_bundle=item.if_bundle or None,
            unless_bundle=item.unless_bundle or None,
            if_title=item.if_title or None,
            unless_title=item.unless_title or None,
        )
        app_label = context.name or "unknown"
        if context.bundle_id:
            app_label = f"{app_label} ({context.bundle_id})"
        click.echo(tf("cli.match.app", app=app_label))
        if allowed:
            click.echo(t("cli.match.allowed_yes"))
        else:
            click.echo(t("cli.match.allowed_no"))
            if item.if_app:
                click.echo(f"if_app: {', '.join(item.if_app)}")
            if item.if_bundle:
                click.echo(f"if_bundle: {', '.join(item.if_bundle)}")
        if not item.ignore_case and trigger not in item.triggers:
            click.echo(
                f"Note: trigger is case-sensitive; configured as {', '.join(item.triggers)}"
            )

    rendered = render_match_interactive(item, app_config=bundle.app)
    if rendered is None:
        raise click.ClickException(t("cli.render_cancelled"))
    click.echo(rendered)


@main.command()
@click.pass_context
def search(ctx: click.Context) -> None:
    """Open the snippet search picker."""
    config_dir: Path = ctx.obj["config_dir"]
    bundle = active_bundle(config_dir, load_config(config_dir))
    items = build_search_items(bundle.matches, bundle.app)
    picked = pick_snippet(items, app_config=bundle.app)
    if not picked:
        raise SystemExit(0)
    text = resolve_snippet_text(picked.match, app_config=bundle.app)
    if text:
        click.echo(text)


@main.command("list")
@click.pass_context
def list_cmd(ctx: click.Context) -> None:
    """List configured snippets."""
    click.echo(format_match_list(ctx.obj["config_dir"]))


@main.command()
@click.argument("trigger")
@click.argument("replace")
@click.option("--file", "target_file", default="dev.yml", show_default=True, help="Match file to update")
@click.option("--if-app", multiple=True, help="Restrict snippet to app names")
@click.option("--unless-app", multiple=True, help="Disable snippet in app names")
@click.pass_context
def add(
    ctx: click.Context,
    trigger: str,
    replace: str,
    target_file: str,
    if_app: tuple[str, ...],
    unless_app: tuple[str, ...],
) -> None:
    """Add a snippet from the command line."""
    try:
        path = append_match(
            ctx.obj["config_dir"],
            trigger,
            replace,
            target_file=target_file,
            if_app=list(if_app) or None,
            unless_app=list(unless_app) or None,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(tf("cli.added", trigger=trigger, path=path))


@main.command("new")
@click.argument("trigger")
@click.option(
    "--template",
    "template_id",
    required=True,
    help="Built-in template id (email, signature, legal-it, dev, meeting)",
)
@click.option("--file", "target_file", default="dev.yml", show_default=True, help="Match file to update")
@click.pass_context
def new_cmd(ctx: click.Context, trigger: str, template_id: str, target_file: str) -> None:
    """Create a snippet from a built-in template."""
    from .match_store import append_match_entry
    from .snippet_templates import build_match_from_template

    try:
        entry = build_match_from_template(template_id, trigger)
        path = append_match_entry(
            ctx.obj["config_dir"],
            entry,
            target_file=target_file,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(tf("cli.created", trigger=trigger, template=template_id, path=path))


@main.group()
def templates() -> None:
    """Built-in snippet templates."""


@templates.command("list")
def templates_list() -> None:
    """List available snippet templates."""
    from .snippet_templates import list_templates

    click.echo(t("cli.templates.header"))
    for item in list_templates():
        click.echo(f"  {item.id:12} {item.name} — {item.description}")


@main.command("import")
@click.argument("source", type=click.Path(exists=True))
@click.option("--force", is_flag=True, help="Overwrite existing match files")
@click.pass_context
def import_cmd(ctx: click.Context, source: str, force: bool) -> None:
    """Import YAML snippet files from a file or directory."""
    try:
        imported = import_matches(ctx.obj["config_dir"], Path(source).expanduser(), force=force)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    echo_imported_files(imported)


@main.command("editor")
@click.pass_context
def editor_cmd(ctx: click.Context) -> None:
    """Open the graphical snippet editor."""
    from .snippet_editor import open_snippet_editor

    open_snippet_editor(ctx.obj["config_dir"])


@main.command("export")
@click.argument("trigger")
@click.option("-o", "--output", type=click.Path(path_type=Path), help="Write YAML to file")
@click.pass_context
def export_cmd(ctx: click.Context, trigger: str, output: Path | None) -> None:
    """Export a snippet as YAML."""
    try:
        payload = export_snippet_yaml(ctx.obj["config_dir"], trigger)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    if output is None:
        click.echo(payload, nl=False)
        return
    output.write_text(payload, encoding="utf-8")
    click.echo(tf("cli.export.written", path=output))


@main.command("duplicate")
@click.argument("trigger")
@click.argument("new_trigger")
@click.option("--file", "target_file", default="dev.yml", show_default=True)
@click.pass_context
def duplicate_cmd(ctx: click.Context, trigger: str, new_trigger: str, target_file: str) -> None:
    """Duplicate an editable snippet with a new trigger."""
    try:
        path = duplicate_snippet(
            ctx.obj["config_dir"],
            trigger,
            new_trigger,
            target_file=target_file,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(
        tf(
            "cli.duplicate.done",
            source=trigger,
            target=new_trigger,
            path=path,
        )
    )


@main.command("stats")
@click.option("--enable", "enable", is_flag=True, help="Start recording local expansion counts")
@click.option("--disable", "disable", is_flag=True, help="Stop recording local expansion counts")
@click.pass_context
def stats_cmd(ctx: click.Context, enable: bool, disable: bool) -> None:
    """Show or toggle opt-in local expansion statistics."""
    from .config import load_app_config
    from .expansion_stats import format_stats_report, set_tracking_enabled
    from .paths import config_file

    config_dir: Path = ctx.obj["config_dir"]
    app = load_app_config(config_file(config_dir))
    if enable and disable:
        raise click.ClickException("Use only one of --enable or --disable")
    if enable:
        if not app.track_expansions:
            raise click.ClickException(t("stats.need_config"))
        set_tracking_enabled(config_dir, True)
        click.echo(t("stats.enabled"))
    if disable:
        set_tracking_enabled(config_dir, False)
        click.echo(t("stats.disabled"))
    click.echo(format_stats_report(config_dir))


@main.command("registry")
@click.option("--json", "as_json", is_flag=True, help="Output JSON catalog")
@click.pass_context
def registry_cmd(ctx: click.Context, as_json: bool) -> None:
    """List hub packages, installed packages, and local plugins."""
    from .registry_catalog import (
        build_registry_catalog,
        format_registry_json,
        format_registry_report,
    )

    catalog = build_registry_catalog(ctx.obj["config_dir"])
    if as_json:
        click.echo(format_registry_json(catalog), nl=False)
    else:
        click.echo(format_registry_report(catalog, config_dir=ctx.obj["config_dir"]))


@main.command("migrate-espanso")
@click.option(
    "--source",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=None,
    help="Espanso config directory (auto-detected if omitted)",
)
@click.option("--force", is_flag=True, help="Overwrite existing imported files")
@click.pass_context
def migrate_espanso_cmd(ctx: click.Context, source: str | None, force: bool) -> None:
    """Import Espanso config with automatic backup and migration report."""
    from .espanso_migrate import migrate_espanso_config

    config_dir: Path = ctx.obj["config_dir"]
    try:
        report = migrate_espanso_config(
            config_dir,
            source=Path(source).expanduser() if source else None,
            force=force,
        )
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc

    echo_espanso_import_report(
        report.import_report,
        backup_path=report.backup_path,
    )


@main.command("import-espanso")
@click.option(
    "--source",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=None,
    help="Espanso config directory (auto-detected if omitted)",
)
@click.option("--force", is_flag=True, help="Overwrite existing imported files")
@click.pass_context
def import_espanso_cmd(ctx: click.Context, source: str | None, force: bool) -> None:
    """Import matches and settings from an Espanso configuration."""
    from .espanso_import import import_espanso_config

    config_dir: Path = ctx.obj["config_dir"]
    try:
        report = import_espanso_config(
            config_dir,
            source=Path(source).expanduser() if source else None,
            force=force,
        )
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc

    echo_espanso_import_report(report)


@main.command("migrate-textexpander")
@click.option(
    "--source",
    type=click.Path(exists=True, dir_okay=True, file_okay=True),
    default=None,
    help="TextExpander CSV, Settings.textexpander, or folder of CSV exports",
)
@click.option("--force", is_flag=True, help="Overwrite existing imported files")
@click.pass_context
def migrate_textexpander_cmd(ctx: click.Context, source: str | None, force: bool) -> None:
    """Import TextExpander snippets with automatic backup and migration report."""
    from .external_import import migrate_textexpander_snippets

    config_dir: Path = ctx.obj["config_dir"]
    try:
        report = migrate_textexpander_snippets(
            config_dir,
            source=Path(source).expanduser() if source else None,
            force=force,
        )
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc

    echo_external_import_report(
        report.import_report,
        backup_path=report.backup_path,
    )


@main.command("import-textexpander")
@click.option(
    "--source",
    type=click.Path(exists=True, dir_okay=True, file_okay=True),
    default=None,
    help="TextExpander CSV, Settings.textexpander, or folder of CSV exports",
)
@click.option("--force", is_flag=True, help="Overwrite existing imported files")
@click.pass_context
def import_textexpander_cmd(ctx: click.Context, source: str | None, force: bool) -> None:
    """Import TextExpander snippets (CSV export or live Settings.textexpander)."""
    from .external_import import import_textexpander_snippets

    config_dir: Path = ctx.obj["config_dir"]
    try:
        report = import_textexpander_snippets(
            config_dir,
            source=Path(source).expanduser() if source else None,
            force=force,
        )
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc

    echo_external_import_report(report)


@main.command("migrate-raycast")
@click.option(
    "--source",
    required=True,
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="Raycast snippets JSON export",
)
@click.option("--force", is_flag=True, help="Overwrite existing imported files")
@click.pass_context
def migrate_raycast_cmd(ctx: click.Context, source: str, force: bool) -> None:
    """Import Raycast snippets JSON with automatic backup and migration report."""
    from .external_import import migrate_raycast_snippets

    config_dir: Path = ctx.obj["config_dir"]
    try:
        report = migrate_raycast_snippets(
            config_dir,
            source=Path(source).expanduser(),
            force=force,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    echo_external_import_report(
        report.import_report,
        backup_path=report.backup_path,
    )


@main.command("import-raycast")
@click.option(
    "--source",
    required=True,
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="Raycast snippets JSON export",
)
@click.option("--force", is_flag=True, help="Overwrite existing imported files")
@click.pass_context
def import_raycast_cmd(ctx: click.Context, source: str, force: bool) -> None:
    """Import Raycast snippets JSON (Export Snippets in Raycast)."""
    from .external_import import import_raycast_snippets

    config_dir: Path = ctx.obj["config_dir"]
    try:
        report = import_raycast_snippets(
            config_dir,
            source=Path(source).expanduser(),
            force=force,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    echo_external_import_report(report)


@main.group()
def hub() -> None:
    """Browse and install snippet packages from the hub."""


@hub.command("list")
@click.pass_context
def hub_list(ctx: click.Context) -> None:
    """List packages available in the hub."""
    from .hub import fetch_registry
    from .packages import list_installed_packages

    config_dir: Path = ctx.obj["config_dir"]
    installed = set(list_installed_packages(match_dir(config_dir)))
    for package in fetch_registry():
        marker = t("cli.hub.installed_marker") if package.id in installed else ""
        click.echo(f"{package.id}: {package.name}{marker}")
        if package.description:
            click.echo(f"  {package.description}")


@hub.command()
@click.argument("query", required=False, default="")
@click.pass_context
def search(ctx: click.Context, query: str) -> None:
    """Search the package hub."""
    from .hub import search_hub_packages

    for package in search_hub_packages(query):
        click.echo(f"{package.id}: {package.name} — {package.description}")


@hub.command()
@click.argument("package_id")
@click.option("--force", is_flag=True, help="Overwrite an installed package")
@click.pass_context
def install(ctx: click.Context, package_id: str, force: bool) -> None:
    """Install a package from the hub."""
    from .hub import install_hub_package

    try:
        path = install_hub_package(ctx.obj["config_dir"], package_id, force=force)
    except (ValueError, FileExistsError, FileNotFoundError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(tf("cli.hub.installed", package=package_id, path=path))


@hub.command()
@click.argument("package_id")
@click.pass_context
def uninstall(ctx: click.Context, package_id: str) -> None:
    """Remove an installed hub package."""
    from .hub import uninstall_hub_package

    if uninstall_hub_package(ctx.obj["config_dir"], package_id):
        click.echo(tf("cli.hub.removed", package=package_id))
    else:
        raise click.ClickException(tf("cli.hub.not_installed", package=package_id))


@hub.command("publish")
@click.argument("package_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--install", is_flag=True, help="Install the package into the local config")
@click.option(
    "--bundle",
    is_flag=True,
    help="Copy into the Expando bundle (default_config/match/packages)",
)
@click.option(
    "--register",
    is_flag=True,
    help="Register package metadata in packages/hub/index.json",
)
@click.pass_context
def hub_publish(
    ctx: click.Context,
    package_dir: Path,
    install: bool,
    bundle: bool,
    register: bool,
) -> None:
    """Validate a local hub package directory and optionally install or bundle it."""
    from .hub import publish_hub_package

    config_dir: Path = ctx.obj["config_dir"]
    report = publish_hub_package(
        package_dir,
        config_dir=config_dir,
        install=install,
        bundle=bundle,
        register=register,
    )
    if report.warnings:
        click.echo(t("cli.hub.publish.warning"))
        for warning in report.warnings:
            click.echo(f"  ! {warning}")

    if not report.ok:
        click.echo(t("cli.hub.publish.error"))
        for error in report.errors:
            click.echo(f"  - {error}")
        raise SystemExit(1)

    click.echo(
        tf("cli.hub.publish.ok", package_id=report.package_id, matches=report.match_count)
    )
    if report.installed_to:
        click.echo(tf("cli.hub.publish.installed", path=report.installed_to))
    if report.bundled_to:
        click.echo(tf("cli.hub.publish.bundled", path=report.bundled_to))
    if report.registered:
        click.echo(t("cli.hub.publish.registered"))


@hub.command()
@click.pass_context
def browse(ctx: click.Context) -> None:
    """Open a visual picker to install hub packages."""
    from .hub import hub_packages_for_picker, install_hub_package
    from .ui_bridge import show_search_picker

    config_dir: Path = ctx.obj["config_dir"]
    picked = show_search_picker(hub_packages_for_picker(config_dir))
    if not picked:
        raise SystemExit(0)
    if picked.get("installed") == "1":
        click.echo(t("cli.hub.already_installed"))
        raise SystemExit(0)
    package_id = picked.get("package_id") or picked.get("trigger")
    if not package_id:
        raise click.ClickException(t("cli.hub.no_selection"))
    try:
        path = install_hub_package(config_dir, str(package_id))
    except (ValueError, FileExistsError, FileNotFoundError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(tf("cli.hub.installed", package=package_id, path=path))


@main.command()
@click.pass_context
def packages(ctx: click.Context) -> None:
    """List installed snippet packages."""
    names = list_installed_packages(match_dir(ctx.obj["config_dir"]))
    if not names:
        click.echo(t("cli.packages.none"))
        return
    for name in names:
        click.echo(name)


@main.command()
@click.option("--output", type=click.Path(), default=None, help="Destination .tar.gz path")
@click.pass_context
def backup(ctx: click.Context, output: str | None) -> None:
    """Backup the configuration directory."""
    destination = backup_config(ctx.obj["config_dir"], Path(output) if output else None)
    click.echo(tf("cli.backup_created", path=destination))


@main.command()
@click.argument("archive", type=click.Path(exists=True))
@click.pass_context
def restore(ctx: click.Context, archive: str) -> None:
    """Restore configuration from a backup archive."""
    restore_config(ctx.obj["config_dir"], Path(archive))
    click.echo(t("cli.restored"))


@main.command()
@click.option("--force", is_flag=True, help="Show the permission wizard again.")
@click.pass_context
def setup(ctx: click.Context, force: bool) -> None:
    """Run the macOS permission onboarding wizard."""
    run_onboarding(ctx.obj["config_dir"], force=force)
    report = run_doctor(ctx.obj["config_dir"])
    click.echo(format_doctor_report(report))


@main.command()
@click.option(
    "--tail",
    "-f",
    is_flag=True,
    help="Follow the log file (like tail -f).",
)
@click.option(
    "--lines",
    "-n",
    default=50,
    show_default=True,
    help="Number of lines to show before following.",
)
@click.pass_context
def logs(ctx: click.Context, tail: bool, lines: int) -> None:
    """Show Expando log output."""
    config_dir: Path = ctx.obj["config_dir"]
    path = log_file(config_dir)
    try:
        print_log_tail(path, lines=lines, follow=tail)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except KeyboardInterrupt:
        raise SystemExit(0) from None


@main.group()
def plugins() -> None:
    """Manage local Python plugins."""


@plugins.command("list")
@click.pass_context
def plugins_list(ctx: click.Context) -> None:
    """List loaded plugin files."""
    from .plugins import PluginManager

    manager = PluginManager(ctx.obj["config_dir"])
    names = manager.list_plugins()
    if not names:
        click.echo(t("cli.plugins.none"))
        return
    for name in names:
        click.echo(name)


@main.command("check-updates")
@click.pass_context
def check_updates_cmd(ctx: click.Context) -> None:
    """Check for app updates via the Sparkle appcast feed."""
    from .config import load_config
    from .updater import check_for_updates, open_download_url

    config_dir: Path = ctx.obj["config_dir"]
    config = load_config(config_dir)
    result = check_for_updates(
        config_dir,
        feed_url=config.app.update_feed_url or None,
        force=True,
        notify_user=False,
    )
    if result.error:
        raise click.ClickException(tf("cli.update.failed", error=result.error))
    if result.available:
        click.echo(tf("cli.update.available", version=result.available.version))
        click.echo(result.available.download_url)
        open_download_url(result.available.download_url)
        return
    click.echo(tf("cli.update.current", version=result.current_version))


@main.command()
@click.option("--count", default=1000, show_default=True, help="Number of synthetic matches")
@click.option(
    "--char-iterations",
    default=10_000,
    show_default=True,
    help="Iterations for handle_char throughput",
)
@click.option(
    "--expand-iterations",
    default=2_000,
    show_default=True,
    help="Iterations for expansion lookup latency",
)
def benchmark(count: int, char_iterations: int, expand_iterations: int) -> None:
    """Benchmark trigger buffer performance under load."""
    from .benchmark import format_benchmark_report, run_engine_benchmark

    try:
        result = run_engine_benchmark(
            match_count=count,
            char_iterations=char_iterations,
            expand_iterations=expand_iterations,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(format_benchmark_report(result))


@main.group()
def crashes() -> None:
    """Inspect local crash reports (never uploaded)."""


@crashes.command("list")
@click.option("--limit", default=10, show_default=True, help="Maximum reports to show")
@click.pass_context
def crashes_list(ctx: click.Context, limit: int) -> None:
    """List recent local crash reports."""
    from .crash_reporting import list_crash_reports
    from .paths import crashes_dir

    config_dir: Path = ctx.obj["config_dir"]
    reports = list_crash_reports(config_dir, limit=limit)
    if not reports:
        click.echo(tf("cli.no_crashes", path=crashes_dir(config_dir)))
        return
    for item in reports:
        stamp = item.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        click.echo(f"{stamp}  {item.exception_type}  [{item.source}]  {item.path.name}")
        if item.message:
            click.echo(f"  {item.message}")


@crashes.command("show")
@click.argument("report", required=False, default="latest")
@click.pass_context
def crashes_show(ctx: click.Context, report: str) -> None:
    """Show a crash report by filename or 'latest'."""
    from .crash_reporting import format_crash_report, list_crash_reports
    from .paths import crashes_dir

    config_dir: Path = ctx.obj["config_dir"]
    directory = crashes_dir(config_dir)
    if report == "latest":
        items = list_crash_reports(config_dir, limit=1)
        if not items:
            raise click.ClickException(t("cli.crash.none"))
        path = items[0].path
    else:
        path = directory / report
        if not path.exists():
            path = directory / f"crash-{report}.json"
        if not path.exists():
            raise click.ClickException(tf("cli.crash.not_found", name=report))
    click.echo(format_crash_report(path))


@main.command("security-audit")
@click.pass_context
def security_audit_cmd(ctx: click.Context) -> None:
    """Review shell allowlist, import paths, and hub TLS configuration."""
    from .security_audit import format_security_audit_report, run_security_audit

    report = run_security_audit(ctx.obj["config_dir"])
    click.echo(format_security_audit_report(report))
    if not report.ok:
        raise SystemExit(1)


@main.command()
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """Validate configuration, permissions, and daemon health."""
    report = run_doctor(ctx.obj["config_dir"])
    click.echo(format_doctor_report(report))
    if not report.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()