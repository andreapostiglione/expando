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


@main.group()
def sync() -> None:
    """Assist optional config sync via git or iCloud Drive."""


@sync.command("status")
@click.pass_context
def sync_status(ctx: click.Context) -> None:
    """Show how the config directory is synced."""
    from .sync_assist import format_sync_report, inspect_sync_status

    click.echo(format_sync_report(inspect_sync_status(ctx.obj["config_dir"])))


@sync.command("init-git")
@click.option("--commit", is_flag=True, help="Create an initial commit")
@click.pass_context
def sync_init_git(ctx: click.Context, commit: bool) -> None:
    """Initialize git in the config directory with a safe .gitignore."""
    from .sync_assist import init_git_sync

    try:
        messages = init_git_sync(ctx.obj["config_dir"], commit=commit)
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc
    for line in messages:
        click.echo(line)


@sync.command("icloud")
@click.option("--folder", "folder_name", default="expando-config", show_default=True)
@click.option("--dry-run", is_flag=True, help="Show planned actions without changing files")
@click.pass_context
def sync_icloud(ctx: click.Context, folder_name: str, dry_run: bool) -> None:
    """Move config to iCloud Drive and symlink the default path."""
    from .sync_assist import setup_icloud_symlink

    try:
        messages = setup_icloud_symlink(
            ctx.obj["config_dir"],
            folder_name=folder_name,
            dry_run=dry_run,
        )
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc
    for line in messages:
        click.echo(line)


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


@hub.command("validate-community")
@click.option("--json", "as_json", is_flag=True, help="Print validation report as JSON")
@click.option("--html", "as_html", is_flag=True, help="Write trigger suggestions HTML dashboard")
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="HTML output path for --html (defaults to docs/hub-trigger-suggestions.html)",
)
def hub_validate_community(as_json: bool, as_html: bool, output: Path | None) -> None:
    """Validate all packages under packages/community (CI pre-submit gate)."""
    import json

    from .hub_marketplace import (
        community_validation_document,
        default_trigger_suggestions_html_path,
        find_community_official_trigger_collisions,
        find_community_official_trigger_similarities,
        find_cross_package_trigger_duplicates,
        format_community_validation_report,
        trigger_similarity_suggestion_to_dict,
        validate_community_hub_packages,
        write_trigger_suggestions_html,
    )

    reports = validate_community_hub_packages()
    trigger_duplicates = find_cross_package_trigger_duplicates()
    official_collisions = find_community_official_trigger_collisions()
    trigger_suggestions = find_community_official_trigger_similarities()
    validation_ok = (
        all(report.ok for _, report in reports)
        and not trigger_duplicates
        and not official_collisions
    )
    if as_html or output is not None:
        destination = output or default_trigger_suggestions_html_path()
        path = write_trigger_suggestions_html(destination)
        click.echo(t("hub.validate.community.html_exported").format(path=path))
        if not as_json:
            if not validation_ok:
                raise SystemExit(1)
            return
    if as_json:
        payload = community_validation_document()
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        if not validation_ok:
            raise SystemExit(1)
        return

    text, ok = format_community_validation_report(
        reports,
        trigger_duplicates=trigger_duplicates,
        official_collisions=official_collisions,
        trigger_suggestions=trigger_suggestions,
    )
    click.echo(text)
    if not ok:
        raise SystemExit(1)


@hub.group("submit", invoke_without_command=True)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Write submission zip to this path (submit alias)",
)
@click.option(
    "--queue",
    is_flag=True,
    help="Add the package to the local marketplace queue (submit alias)",
)
@click.pass_context
def hub_submit_group(ctx: click.Context, output: Path | None, queue: bool) -> None:
    """Prepare and track marketplace package submissions."""
    if ctx.invoked_subcommand is not None:
        return
    if not ctx.args:
        click.echo(ctx.get_help())
        ctx.exit(0)
    if len(ctx.args) > 1:
        raise click.ClickException(f"Unexpected arguments: {' '.join(ctx.args[1:])}")
    package_dir = click.Path(exists=True, file_okay=False, path_type=Path)(ctx.args[0])
    ctx.invoke(
        hub_submit_run,
        package_dir=package_dir,
        output=output,
        queue=queue,
        as_json=False,
    )


@hub_submit_group.command("run")
@click.argument("package_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Write submission zip to this path",
)
@click.option(
    "--queue",
    is_flag=True,
    help="Add the package to the local marketplace queue as pending",
)
@click.option("--json", "as_json", is_flag=True, help="Print submission result as JSON")
@click.pass_context
def hub_submit_run(
    ctx: click.Context,
    package_dir: Path,
    output: Path | None,
    queue: bool,
    as_json: bool,
) -> None:
    """Validate, bundle, and optionally queue a contributor submission."""
    import json

    from .hub import validate_hub_package_dir
    from .hub_marketplace import (
        contributor_submission_to_dict,
        format_submission_instructions,
        run_contributor_submission_workflow,
    )

    report = validate_hub_package_dir(package_dir)
    if not report.ok:
        raise click.ClickException("; ".join(report.errors))
    bundle_path = output or (
        ctx.obj["config_dir"] / f"hub-submit-{report.package_id}.zip"
    )
    try:
        result = run_contributor_submission_workflow(
            package_dir,
            bundle_path=bundle_path,
            queue=queue,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if queue and not as_json:
        from .i18n import t

        click.echo(t("hub.submit.queued").format(package_id=result.package_id))
    if as_json:
        click.echo(json.dumps(contributor_submission_to_dict(result), indent=2, ensure_ascii=False))
    else:
        from .hub_marketplace import HubSubmission

        submission = HubSubmission(
            package_id=result.package_id,
            bundle_path=result.bundle_path,
            manifest=result.manifest,
            match_count=result.match_count,
        )
        click.echo(format_submission_instructions(submission, bundle_path=result.bundle_path))


@hub_submit_group.command("init")
@click.argument("package_id")
@click.option("--name", default=None, help="Display name (defaults to package id)")
@click.option("--description", default=None, help="Short package description")
@click.option("--author", default="Community", show_default=True)
@click.option("--tag", "tags", multiple=True, help="Tag to include in hub.json (repeatable)")
@click.option(
    "-o",
    "--output",
    type=click.Path(file_okay=False, path_type=Path),
    default=".",
    show_default=True,
    help="Parent directory for the new package folder",
)
@click.option("--force", is_flag=True, help="Overwrite files in an existing package directory")
def hub_submit_init(
    package_id: str,
    name: str | None,
    description: str | None,
    author: str,
    tags: tuple[str, ...],
    output: Path,
    force: bool,
) -> None:
    """Scaffold a new community hub package template."""
    from .hub_marketplace import init_contributor_package
    from .i18n import t

    display_name = name or package_id.replace("-", " ").title()
    package_description = description or f"Community snippets package {package_id}"
    try:
        package_dir = init_contributor_package(
            output,
            package_id,
            name=display_name,
            description=package_description,
            author=author,
            tags=list(tags) if tags else None,
            force=force,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(t("hub.submit.init.ok").format(path=package_dir))
    click.echo(t("hub.submit.init.next").format(path=package_dir))


@hub_submit_group.command("status")
@click.argument("package_id")
@click.option("--json", "as_json", is_flag=True, help="Print status as JSON")
def hub_submit_status(package_id: str, as_json: bool) -> None:
    """Show marketplace review status for a submitted package."""
    import json

    from .hub_marketplace import (
        contributor_submission_status,
        contributor_submission_status_to_dict,
        format_submission_status_report,
    )

    report = contributor_submission_status(package_id)
    if as_json:
        click.echo(
            json.dumps(contributor_submission_status_to_dict(report), indent=2, ensure_ascii=False)
        )
    else:
        click.echo(format_submission_status_report(report))


@hub.group("review")
def hub_review() -> None:
    """Review pending marketplace submissions (maintainers)."""


@hub_review.command("list")
@click.option(
    "--status",
    default="pending",
    show_default=True,
    type=click.Choice(["pending", "approved", "rejected", "all"]),
)
def hub_review_list(status: str) -> None:
    """List marketplace submissions by review status."""
    from .hub_marketplace import format_review_queue_report, list_marketplace_queue

    if status == "all":
        lines = []
        for value in ("pending", "approved", "rejected"):
            packages = list_marketplace_queue(status=value)
            lines.append(format_review_queue_report(packages, status=value))
        click.echo("\n\n".join(lines))
        return
    packages = list_marketplace_queue(status=status)
    click.echo(format_review_queue_report(packages, status=status))


@hub_review.command("queue")
@click.argument("package_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
def hub_review_queue(package_dir: Path) -> None:
    """Add a validated package to the local marketplace queue as pending."""
    from .hub_marketplace import queue_marketplace_submission

    try:
        package = queue_marketplace_submission(package_dir)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(t("hub.review.queued").format(package_id=package.id))


@hub_review.command("approve")
@click.argument("package_id")
@click.option("--reviewer", default="", help="Reviewer name or handle")
@click.option("--note", default="", help="Optional review note")
def hub_review_approve(package_id: str, reviewer: str, note: str) -> None:
    """Approve a pending marketplace package."""
    from .hub_marketplace import review_marketplace_package

    try:
        package = review_marketplace_package(
            package_id,
            "approve",
            reviewer=reviewer,
            note=note,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(t("hub.review.approved").format(package_id=package.id))


@hub_review.command("reject")
@click.argument("package_id")
@click.option("--reviewer", default="", help="Reviewer name or handle")
@click.option("--note", default="", help="Optional rejection reason")
def hub_review_reject(package_id: str, reviewer: str, note: str) -> None:
    """Reject a pending marketplace package."""
    from .hub_marketplace import review_marketplace_package

    try:
        package = review_marketplace_package(
            package_id,
            "reject",
            reviewer=reviewer,
            note=note,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(t("hub.review.rejected").format(package_id=package.id))


@hub.group("portal")
def hub_portal() -> None:
    """Manage remote marketplace index export and sync."""


@hub_portal.command("status")
def hub_portal_status() -> None:
    """Show local marketplace path, remote URL, and queue counts."""
    from .hub_marketplace import format_portal_status_report, marketplace_portal_stats

    click.echo(format_portal_status_report(marketplace_portal_stats()))


@hub_portal.command("export")
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Write publishable JSON index (defaults to packages/hub/marketplace-published.json)",
)
def hub_portal_export(output: Path | None) -> None:
    """Export approved packages as a JSON index for remote hosting."""
    from .hub_marketplace import export_portal_index
    from .paths import package_root

    destination = output or (package_root() / "packages" / "hub" / "marketplace-published.json")
    path = export_portal_index(destination)
    click.echo(t("hub.portal.exported").format(path=path))


@hub_portal.command("sync")
@click.option("--dry-run", is_flag=True, help="Show merge stats without writing local index")
def hub_portal_sync(dry_run: bool) -> None:
    """Merge a remote marketplace index into the local queue file."""
    from .hub_marketplace import sync_remote_marketplace_index

    try:
        stats = sync_remote_marketplace_index(dry_run=dry_run)
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc
    prefix = t("hub.portal.dry_run") if dry_run else t("hub.portal.synced")
    click.echo(
        f"{prefix}: "
        + t("hub.portal.sync_stats").format(
            added=stats["added"],
            updated=stats["updated"],
            unchanged=stats["unchanged"],
        )
    )


@hub_portal.command("pending-diff")
@click.option("--json", "as_json", is_flag=True, help="Print pending metadata diff as JSON")
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Write pending metadata diff JSON to this path",
)
def hub_portal_pending_diff(as_json: bool, output: Path | None) -> None:
    """Export remote vs local pending metadata differences as JSON."""
    import json

    from .hub_marketplace import (
        format_marketplace_pending_diff_report,
        marketplace_pending_metadata_diff_document,
        write_marketplace_pending_diff_json,
    )

    if as_json or output is not None:
        payload = marketplace_pending_metadata_diff_document()
        text = json.dumps(payload, indent=2, ensure_ascii=False)
        if output is not None:
            write_marketplace_pending_diff_json(output)
            if not as_json:
                click.echo(t("hub.portal.pending_diff.exported").format(path=output))
        if as_json:
            click.echo(text)
        return

    click.echo(format_marketplace_pending_diff_report())


@hub_portal.command("publish-site")
@click.option(
    "--html",
    "html_path",
    type=click.Path(path_type=Path),
    help="Write marketplace HTML (defaults to docs/hub-marketplace.html)",
)
@click.option(
    "--json",
    "json_path",
    type=click.Path(path_type=Path),
    help="Write marketplace JSON (defaults to docs/hub/marketplace.json)",
)
def hub_portal_publish_site(html_path: Path | None, json_path: Path | None) -> None:
    """Generate GitHub Pages marketplace site and JSON index."""
    from .hub_marketplace import build_publishable_portal_index, publish_portal_site

    payload = build_publishable_portal_index()
    paths = publish_portal_site(html_path=html_path, json_path=json_path)
    click.echo(
        t("hub.portal.published").format(
            html=paths["html"],
            json=paths["json"],
            suggestions=paths["suggestions_html"],
            maintainer=paths["maintainer_html"],
            validation=paths["validation_json"],
            health_html=paths["health_html"],
            health_json=paths["health_json"],
            hub_index=paths["hub_index_json"],
            count=len(payload.get("packages", [])),
        )
    )


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
@click.option(
    "--sparkle",
    is_flag=True,
    help="Include Sparkle/appcast update-check benchmark (distribution builds)",
)
@click.option(
    "--feed-url",
    default=None,
    help="Override Sparkle appcast URL for --sparkle",
)
@click.option(
    "--sparkle-warn-ms",
    type=int,
    default=None,
    help="Warn when Sparkle helper check exceeds this latency (ms)",
)
@click.option(
    "--sparkle-fail-ms",
    type=int,
    default=None,
    help="Fail when Sparkle helper check exceeds this latency (ms)",
)
def benchmark(
    count: int,
    char_iterations: int,
    expand_iterations: int,
    sparkle: bool,
    feed_url: str | None,
    sparkle_warn_ms: int | None,
    sparkle_fail_ms: int | None,
) -> None:
    """Benchmark trigger buffer performance under load."""
    from .benchmark import (
        format_benchmark_report,
        format_sparkle_benchmark_report,
        run_engine_benchmark,
        run_sparkle_update_benchmark,
    )

    try:
        result = run_engine_benchmark(
            match_count=count,
            char_iterations=char_iterations,
            expand_iterations=expand_iterations,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(format_benchmark_report(result))
    if sparkle:
        from .benchmark import (
            resolve_sparkle_helper_fail_ms,
            resolve_sparkle_helper_warn_ms,
            sparkle_helper_latency_fail,
        )

        warn_ms = sparkle_warn_ms
        if warn_ms is None:
            warn_ms = resolve_sparkle_helper_warn_ms()
        fail_ms = sparkle_fail_ms
        if fail_ms is None:
            fail_ms = resolve_sparkle_helper_fail_ms()
        sparkle_result = run_sparkle_update_benchmark(feed_url=feed_url)
        click.echo("")
        click.echo(
            format_sparkle_benchmark_report(
                sparkle_result,
                warn_ms=warn_ms,
                fail_ms=fail_ms,
            )
        )
        if sparkle_helper_latency_fail(sparkle_result.helper_check_ms, fail_ms):
            raise SystemExit(1)


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


@main.command("sparkle-smoke")
@click.option(
    "--app",
    "app_bundle",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path),
    help="Path to Expando.app (defaults to repo or /Applications)",
)
def sparkle_smoke_cmd(app_bundle: Path | None) -> None:
    """Smoke-test Sparkle helper embed (codesign + framework) in a built app."""
    from .sparkle_native import (
        format_sparkle_smoke_report,
        resolve_distribution_app_bundle,
        smoke_test_sparkle_embed,
    )

    bundle = app_bundle
    if bundle is None:
        bundle = resolve_distribution_app_bundle()
    if bundle is None:
        raise click.ClickException(
            "Expando.app not found — pass --app or set EXPANDO_APP_BUNDLE"
        )
    report = smoke_test_sparkle_embed(bundle)
    click.echo(format_sparkle_smoke_report(report))
    if not report.ok:
        raise SystemExit(1)


@main.command("notarize-audit")
@click.option(
    "--app",
    "app_bundle",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path),
    help="Path to Expando.app (defaults to repo or /Applications)",
)
@click.option(
    "--dmg",
    "dmg",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, path_type=Path),
    help="Path to Expando.dmg",
)
@click.option("--strict", is_flag=True, help="Fail when artifacts are missing")
@click.option("--json", "as_json", is_flag=True, help="Print the audit report as JSON")
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Write JSON audit report to this file",
)
@click.option(
    "--record",
    is_flag=True,
    help="Append this audit run to local notarize-audit-history.json",
)
@click.option(
    "--svg",
    is_flag=True,
    help="Write notarization trend SVG (notarize-audit-trend.svg)",
)
@click.option(
    "--svg-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Override SVG output path (implies --svg)",
)
@click.pass_context
def notarize_audit_cmd(
    ctx: click.Context,
    app_bundle: Path | None,
    dmg: Path | None,
    strict: bool,
    as_json: bool,
    output: Path | None,
    record: bool,
    svg: bool,
    svg_path: Path | None,
) -> None:
    """Audit codesign, entitlements, Gatekeeper, and notarization staples."""
    import json

    from .notarization_audit import (
        format_notarization_audit_report,
        notarization_audit_report_to_dict,
        resolve_audit_targets,
        run_notarization_audit,
        write_notarization_audit_json,
    )

    report = run_notarization_audit(app_bundle=app_bundle, dmg=dmg, strict=strict)
    if output is not None:
        write_notarization_audit_json(report, output)
    if record:
        from .notarization_history import record_notarization_audit

        resolved_app, resolved_dmg = resolve_audit_targets(app_bundle=app_bundle, dmg=dmg)
        entry = record_notarization_audit(
            ctx.obj["config_dir"],
            report,
            app_bundle=resolved_app,
            dmg=resolved_dmg,
        )
        if not as_json:
            click.echo(
                t("notarize.history.recorded").format(
                    path=ctx.obj["config_dir"] / "notarize-audit-history.json",
                    recorded_at=entry["recorded_at"],
                )
            )
    if svg or svg_path is not None:
        from .notarization_history import (
            default_trend_svg_path,
            write_notarization_history_trend_svg,
        )

        svg_destination = write_notarization_history_trend_svg(
            ctx.obj["config_dir"],
            svg_path or default_trend_svg_path(ctx.obj["config_dir"]),
        )
        if not as_json:
            click.echo(t("notarize.history.svg_written").format(path=svg_destination))
    if as_json:
        click.echo(json.dumps(notarization_audit_report_to_dict(report), indent=2, ensure_ascii=False))
    else:
        click.echo(format_notarization_audit_report(report))
    if not report.ok:
        raise SystemExit(1)


@main.group("sparkle-benchmark-history", invoke_without_command=True)
@click.option("--limit", default=10, show_default=True, help="Recent entries to show")
@click.option("--json", "as_json", is_flag=True, help="Print history as JSON")
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Write JSON history export to this file",
)
@click.option(
    "--history-path",
    type=click.Path(path_type=Path),
    help="Sparkle benchmark history file (defaults to repo sparkle-benchmark-history.json)",
)
@click.option(
    "--svg",
    is_flag=True,
    help="Write latency trend SVG (sparkle-benchmark-trend.svg)",
)
@click.option(
    "--svg-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Override SVG output path (implies --svg)",
)
@click.pass_context
def sparkle_benchmark_history_group(
    ctx: click.Context,
    limit: int,
    as_json: bool,
    output: Path | None,
    history_path: Path | None,
    svg: bool,
    svg_path: Path | None,
) -> None:
    """Show or record Sparkle helper benchmark history across releases."""
    if ctx.invoked_subcommand is not None:
        return

    import json

    from .sparkle_benchmark_history import (
        default_trend_svg_path,
        format_sparkle_benchmark_history_report,
        sparkle_benchmark_history_to_dict,
        write_sparkle_benchmark_trend_svg,
    )

    if svg or svg_path is not None:
        svg_destination = write_sparkle_benchmark_trend_svg(
            svg_path or default_trend_svg_path(),
            history_path=history_path,
        )
        click.echo(t("sparkle.benchmark.history.svg_written").format(path=svg_destination))

    if as_json or output is not None:
        payload = sparkle_benchmark_history_to_dict(history_path, limit=limit)
        text = json.dumps(payload, indent=2, ensure_ascii=False)
        if output is not None:
            output = output.expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text + "\n", encoding="utf-8")
            if not as_json:
                click.echo(t("sparkle.benchmark.history.exported").format(path=output))
        if as_json:
            click.echo(text)
        return

    click.echo(format_sparkle_benchmark_history_report(history_path, limit=limit))


@sparkle_benchmark_history_group.command("record")
@click.option("--version", required=True, help="Expando version recorded with this benchmark")
@click.option("--tag", default=None, help="Release tag (defaults to v{version})")
@click.option(
    "--sparkle-warn-ms",
    type=int,
    default=None,
    help="Slow-helper warning threshold in milliseconds",
)
@click.option(
    "--sparkle-fail-ms",
    type=int,
    default=None,
    help="Fail threshold in milliseconds (stored in history; does not exit non-zero)",
)
@click.option("--feed-url", default=None, help="Override Sparkle appcast URL")
@click.option(
    "--history-path",
    type=click.Path(path_type=Path),
    help="Sparkle benchmark history file (defaults to repo sparkle-benchmark-history.json)",
)
@click.option(
    "--svg",
    is_flag=True,
    help="Write latency trend SVG (sparkle-benchmark-trend.svg)",
)
@click.option(
    "--svg-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Override SVG output path (implies --svg)",
)
def sparkle_benchmark_history_record(
    version: str,
    tag: str | None,
    sparkle_warn_ms: int | None,
    sparkle_fail_ms: int | None,
    feed_url: str | None,
    history_path: Path | None,
    svg: bool,
    svg_path: Path | None,
) -> None:
    """Run Sparkle benchmark and append result to release history."""
    from .benchmark import (
        format_sparkle_benchmark_report,
        resolve_sparkle_helper_fail_ms,
        resolve_sparkle_helper_warn_ms,
        run_sparkle_update_benchmark,
    )
    from .sparkle_benchmark_history import (
        default_history_path,
        default_trend_svg_path,
        record_sparkle_benchmark,
        write_sparkle_benchmark_trend_svg,
    )

    warn_ms = sparkle_warn_ms
    if warn_ms is None:
        warn_ms = resolve_sparkle_helper_warn_ms()
    fail_ms = sparkle_fail_ms
    if fail_ms is None:
        fail_ms = resolve_sparkle_helper_fail_ms()
    result = run_sparkle_update_benchmark(feed_url=feed_url)
    click.echo(format_sparkle_benchmark_report(result, warn_ms=warn_ms, fail_ms=fail_ms))
    path = history_path or default_history_path()
    entry = record_sparkle_benchmark(
        result,
        path,
        version=version,
        warn_ms=warn_ms,
        fail_ms=fail_ms,
        tag=tag,
    )
    click.echo(
        t("sparkle.benchmark.history.recorded").format(
            path=path,
            recorded_at=entry.get("recorded_at", "?"),
        )
    )
    if svg or svg_path is not None:
        svg_destination = write_sparkle_benchmark_trend_svg(
            svg_path or default_trend_svg_path(),
            history_path=path,
        )
        click.echo(t("sparkle.benchmark.history.svg_written").format(path=svg_destination))


@main.command("notarize-history")
@click.option("--limit", default=10, show_default=True, help="Recent entries to show")
@click.option("--json", "as_json", is_flag=True, help="Print history as JSON")
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Write JSON history export to this file",
)
@click.option(
    "--svg",
    is_flag=True,
    help="Write notarization trend SVG (notarize-audit-trend.svg)",
)
@click.option(
    "--svg-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Override SVG output path (implies --svg)",
)
@click.pass_context
def notarize_history_cmd(
    ctx: click.Context,
    limit: int,
    as_json: bool,
    output: Path | None,
    svg: bool,
    svg_path: Path | None,
) -> None:
    """Show local notarization audit history and trend."""
    import json

    from .notarization_history import (
        default_trend_svg_path,
        format_notarization_history_report,
        notarization_history_to_dict,
        write_notarization_history_trend_svg,
    )

    config_dir: Path = ctx.obj["config_dir"]
    if svg or svg_path is not None:
        svg_destination = write_notarization_history_trend_svg(
            config_dir,
            svg_path or default_trend_svg_path(config_dir),
            limit=limit,
        )
        click.echo(t("notarize.history.svg_written").format(path=svg_destination))

    if as_json or output is not None:
        payload = notarization_history_to_dict(config_dir, limit=limit)
        text = json.dumps(payload, indent=2, ensure_ascii=False)
        if output is not None:
            output = output.expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text + "\n", encoding="utf-8")
            if not as_json:
                click.echo(t("notarize.history.exported").format(path=output))
        if as_json:
            click.echo(text)
        return

    click.echo(format_notarization_history_report(config_dir, limit=limit))


@main.command()
@click.option(
    "--doctor-json",
    is_flag=True,
    help="Export full doctor diagnostics as structured JSON",
)
@click.option(
    "--doctor-output",
    type=click.Path(path_type=Path),
    help="Write doctor JSON report to this path",
)
@click.option(
    "--marketplace-json",
    is_flag=True,
    help="Export marketplace health (remote stats, sync preview, pending diff) as JSON",
)
@click.option(
    "-o",
    "--marketplace-output",
    type=click.Path(path_type=Path),
    help="Write marketplace JSON report to this path",
)
@click.option(
    "--full-json",
    is_flag=True,
    help="Export full health JSON (doctor, marketplace, histories, community validation)",
)
@click.option(
    "--full-output",
    type=click.Path(path_type=Path),
    help="Write full health JSON report to this path",
)
@click.option(
    "--full-html",
    is_flag=True,
    help="Write full health HTML dashboard (doctor-health.html)",
)
@click.option(
    "--full-html-output",
    type=click.Path(path_type=Path),
    help="Override full health HTML output path (implies --full-html)",
)
@click.pass_context
def doctor(
    ctx: click.Context,
    doctor_json: bool,
    doctor_output: Path | None,
    marketplace_json: bool,
    marketplace_output: Path | None,
    full_json: bool,
    full_output: Path | None,
    full_html: bool,
    full_html_output: Path | None,
) -> None:
    """Validate configuration, permissions, and daemon health."""
    import json

    config_dir: Path = ctx.obj["config_dir"]
    report = run_doctor(config_dir)
    text_report = format_doctor_report(report)

    if (
        full_json
        or full_output is not None
        or full_html
        or full_html_output is not None
    ):
        from .doctor_checks import (
            default_doctor_full_html_path,
            doctor_full_document,
            write_doctor_full_html,
        )

        payload = doctor_full_document(config_dir)
        if full_output is not None:
            json_text = json.dumps(payload, indent=2, ensure_ascii=False)
            full_output = full_output.expanduser().resolve()
            full_output.parent.mkdir(parents=True, exist_ok=True)
            full_output.write_text(json_text + "\n", encoding="utf-8")
            click.echo(t("doctor.full.exported").format(path=full_output))
        if full_html or full_html_output is not None:
            html_path = write_doctor_full_html(
                config_dir,
                full_html_output or default_doctor_full_html_path(),
            )
            click.echo(t("doctor.full.html_exported").format(path=html_path))
        click.echo(text_report)
        if full_json:
            click.echo("")
            click.echo(t("doctor.full.json_section"))
            click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        if not report.ok:
            raise SystemExit(1)
        return

    if marketplace_json or marketplace_output is not None:
        from .doctor_checks import doctor_combined_document

        payload = doctor_combined_document(config_dir)
        json_text = json.dumps(payload, indent=2, ensure_ascii=False)
        if marketplace_output is not None:
            marketplace_output = marketplace_output.expanduser().resolve()
            marketplace_output.parent.mkdir(parents=True, exist_ok=True)
            marketplace_output.write_text(json_text + "\n", encoding="utf-8")
            click.echo(t("doctor.marketplace.exported").format(path=marketplace_output))
        click.echo(text_report)
        if marketplace_json:
            click.echo("")
            click.echo(t("doctor.marketplace.json_section"))
            click.echo(json_text)
        if not report.ok:
            raise SystemExit(1)
        return

    if doctor_json or doctor_output is not None:
        from .doctor_checks import doctor_document

        payload = doctor_document(config_dir)
        json_text = json.dumps(payload, indent=2, ensure_ascii=False)
        if doctor_output is not None:
            doctor_output = doctor_output.expanduser().resolve()
            doctor_output.parent.mkdir(parents=True, exist_ok=True)
            doctor_output.write_text(json_text + "\n", encoding="utf-8")
            click.echo(t("doctor.json.exported").format(path=doctor_output))
        click.echo(text_report)
        if doctor_json:
            click.echo("")
            click.echo(t("doctor.json.section"))
            click.echo(json_text)
        if not report.ok:
            raise SystemExit(1)
        return

    click.echo(text_report)
    if not report.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()