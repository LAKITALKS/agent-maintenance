"""CLI entry point for agent-maintenance."""

import typer

from agent_maintenance import __version__
from agent_maintenance.cli.forge import app as forge_app
from agent_maintenance.cli.loadout import app as loadout_app

app = typer.Typer(
    name="agent-maintenance",
    help=(
        "Maintain and prepare local skill libraries for coding agents.\n\n"
        "Use 'forge' to clean up your skill library, "
        "'loadout' to prepare a focused context for a task."
    ),
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)

app.add_typer(forge_app, name="forge", help="Maintain your skill library.")
app.add_typer(loadout_app, name="loadout", help="Prepare a focused skill context for a task.")


def _version_callback(show: bool) -> None:
    if show:
        typer.echo(f"agent-maintenance {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=_version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    pass
