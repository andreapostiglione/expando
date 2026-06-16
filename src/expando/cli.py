from __future__ import annotations

import os
import subprocess
from pathlib import Path

import click

from . import __version__
from .daemon import is_running, start_daemon, stop_daemon
from .paths import config_file, default_config_dir, ensure_default_config, match_dir, package_root
from .renderer import render_match
from .config import load_config, load_matches


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
        click.echo(f"expando is running (pid {pid})")
    else:
        click.echo("expando is not running")


@main.command()
@click.pass_context
def start(ctx: click.Context) -> None:
    """Start the background daemon."""
    config_dir: Path = ctx.obj["config_dir"]
    pid = start_daemon(config_dir)
    click.echo(f"expando started (pid {pid})")


@main.command()
@click.pass_context
def stop(ctx: click.Context) -> None:
    """Stop the background daemon."""
    config_dir: Path = ctx.obj["config_dir"]
    if stop_daemon(config_dir):
        click.echo("expando stopped")
    else:
        click.echo("expando was not running")


@main.command()
@click.pass_context
def restart(ctx: click.Context) -> None:
    """Restart the background daemon."""
    config_dir: Path = ctx.obj["config_dir"]
    stop_daemon(config_dir)
    pid = start_daemon(config_dir)
    click.echo(f"expando restarted (pid {pid})")


@main.command()
@click.pass_context
def run(ctx: click.Context) -> None:
    """Run in foreground (for debugging)."""
    from .daemon import foreground

    foreground(ctx.obj["config_dir"])


@main.command("match")
@click.argument("trigger")
@click.pass_context
def match_cmd(ctx: click.Context, trigger: str) -> None:
    """Test-render a trigger without typing."""
    config_dir: Path = ctx.obj["config_dir"]
    matches = load_matches(match_dir(config_dir))
    for item in matches:
        if trigger in item.triggers:
            click.echo(render_match(item))
            return
    raise click.ClickException(f"Trigger not found: {trigger}")


@main.command()
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """Validate configuration and show match count."""
    config_dir: Path = ctx.obj["config_dir"]
    bundle = load_config(config_dir)
    click.echo(f"Config dir: {config_dir}")
    click.echo(f"Matches loaded: {len(bundle.matches)}")
    click.echo(f"Toggle key: {bundle.app.toggle_key}")
    click.echo(f"Backend: {bundle.app.backend}")
    click.echo(f"Auto restart: {bundle.app.auto_restart}")
    for item in bundle.matches:
        click.echo(f"  - {', '.join(item.triggers)}")


if __name__ == "__main__":
    main()